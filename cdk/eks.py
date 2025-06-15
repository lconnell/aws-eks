import os
from dotenv import load_dotenv
from aws_cdk import (
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    App, Stack, CfnOutput, Environment, Tags
)
from aws_cdk.lambda_layer_kubectl_v32 import KubectlV32Layer

# Load environment variables from .env file
load_dotenv()

class EksClusterStack(Stack):
    def __init__(self, scope: App, construct_id: str, environment: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get environment from .env file or parameter
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "staging")

        # Environment-specific configuration from .env variables
        config = {
            "staging": {
                "instance_type": os.getenv("STAGING_INSTANCE_TYPE", "t3.medium"),
                "min_size": int(os.getenv("STAGING_MIN_SIZE", "1")),
                "max_size": int(os.getenv("STAGING_MAX_SIZE", "3")),
                "desired_size": int(os.getenv("STAGING_DESIRED_SIZE", "2")),
                "nat_gateways": int(os.getenv("STAGING_NAT_GATEWAYS", "1")),
            },
            "production": {
                "instance_type": os.getenv("PRODUCTION_INSTANCE_TYPE", "m5.large"),
                "min_size": int(os.getenv("PRODUCTION_MIN_SIZE", "2")),
                "max_size": int(os.getenv("PRODUCTION_MAX_SIZE", "10")),
                "desired_size": int(os.getenv("PRODUCTION_DESIRED_SIZE", "3")),
                "nat_gateways": int(os.getenv("PRODUCTION_NAT_GATEWAYS", "3")),
            }
        }
        
        env_config = config.get(environment, config["staging"])
        
        # Get common configuration from .env
        node_disk_size = int(os.getenv("NODE_DISK_SIZE", "100"))
        node_ami_type = os.getenv("NODE_AMI_TYPE", "AL2_x86_64")
        vpc_max_azs = int(os.getenv("VPC_MAX_AZS", "3"))
        vpc_cidr = os.getenv("VPC_CIDR", "10.0.0.0/16")
        enable_vpc_endpoints = os.getenv("ENABLE_VPC_ENDPOINTS", "true").lower() == "true"
        enable_cluster_logging = os.getenv("ENABLE_CLUSTER_LOGGING", "true").lower() == "true"
        enable_public_endpoint = os.getenv("ENABLE_PUBLIC_ENDPOINT", "true").lower() == "true"
        enable_private_endpoint = os.getenv("ENABLE_PRIVATE_ENDPOINT", "true").lower() == "true"
        cluster_name_prefix = os.getenv("CLUSTER_NAME_PREFIX", "eks-cluster")
        
        # Tag configuration
        tag_project = os.getenv("TAG_PROJECT", "EKS-CDK")
        tag_managed_by = os.getenv("TAG_MANAGED_BY", "CDK")
        tag_cost_center = os.getenv("TAG_COST_CENTER", "engineering")
        
        # Create VPC with environment-specific settings
        vpc = ec2.Vpc(
            self, 
            f"EksVpc-{environment}",
            vpc_name=f"eks-vpc-{environment}",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=vpc_max_azs,
            nat_gateways=env_config["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Define the kubectl layer
        kubectl = KubectlV32Layer(self, "KubectlLayer")

        # Create IAM role for EKS cluster
        cluster_role = iam.Role(
            self,
            f"EksClusterRole-{environment}",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy")
            ]
        )

        # Configure endpoint access
        if enable_public_endpoint and enable_private_endpoint:
            endpoint_access = eks.EndpointAccess.PUBLIC_AND_PRIVATE
        elif enable_public_endpoint:
            endpoint_access = eks.EndpointAccess.PUBLIC
        else:
            endpoint_access = eks.EndpointAccess.PRIVATE

        # Configure cluster logging
        cluster_logging_types = []
        if enable_cluster_logging:
            cluster_logging_types = [
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
                eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                eks.ClusterLoggingTypes.SCHEDULER
            ]

        # Define the EKS cluster
        cluster = eks.Cluster(
            self,
            f"EksCluster-{environment}",
            cluster_name=f"{cluster_name_prefix}-{environment}",
            vpc=vpc,
            default_capacity=0,
            version=eks.KubernetesVersion.V1_32,
            kubectl_layer=kubectl,
            role=cluster_role,
            endpoint_access=endpoint_access,
            masters_role=iam.Role.from_role_arn(
                self,
                "MastersRole",
                role_arn=os.getenv("EKS_ADMIN_ROLE_ARN") or os.getenv("EKS_ADMIN_USER_ARN", "")
            ) if (os.getenv("EKS_ADMIN_ROLE_ARN") or os.getenv("EKS_ADMIN_USER_ARN")) else None,
            cluster_logging=cluster_logging_types
        )

        # Map AMI type string to CDK enum
        ami_type_mapping = {
            "AL2_x86_64": eks.NodegroupAmiType.AL2_X86_64,
            "AL2023_x86_64_STANDARD": eks.NodegroupAmiType.AL2023_X86_64_STANDARD,
            "BOTTLEROCKET_x86_64": eks.NodegroupAmiType.BOTTLEROCKET_X86_64,
            "AL2_ARM_64": eks.NodegroupAmiType.AL2_ARM_64,
            "AL2023_ARM_64_STANDARD": eks.NodegroupAmiType.AL2023_ARM_64_STANDARD,
            "BOTTLEROCKET_ARM_64": eks.NodegroupAmiType.BOTTLEROCKET_ARM_64
        }
        
        # Add managed node group
        node_group = cluster.add_nodegroup_capacity(
            f"Nodegroup-{environment}",
            nodegroup_name=f"eks-nodegroup-{environment}",
            instance_types=[ec2.InstanceType(env_config["instance_type"])],
            min_size=env_config["min_size"],
            max_size=env_config["max_size"],
            desired_size=env_config["desired_size"],
            disk_size=node_disk_size,
            ami_type=ami_type_mapping.get(node_ami_type, eks.NodegroupAmiType.AL2_X86_64),
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            tags={
                "Environment": environment,
                "Project": tag_project,
                "ManagedBy": tag_managed_by,
                "CostCenter": tag_cost_center
            }
        )

        # Add VPC endpoints for cost optimization (if enabled)
        if enable_vpc_endpoints:
            vpc.add_gateway_endpoint("S3Endpoint",
                service=ec2.GatewayVpcEndpointAwsService.S3
            )
            
            vpc.add_interface_endpoint("Ec2Endpoint",
                service=ec2.InterfaceVpcEndpointAwsService.EC2
            )
            
            vpc.add_interface_endpoint("StsEndpoint",
                service=ec2.InterfaceVpcEndpointAwsService.STS
            )

        # Add tags to all resources
        Tags.of(self).add("Environment", environment)
        Tags.of(self).add("Project", tag_project)
        Tags.of(self).add("ManagedBy", tag_managed_by)
        Tags.of(self).add("CostCenter", tag_cost_center)

        # Outputs
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ClusterEndpoint", value=cluster.cluster_endpoint)
        CfnOutput(self, "ClusterArn", value=cluster.cluster_arn)
        CfnOutput(self, "VpcId", value=vpc.vpc_id)
        CfnOutput(self, "NodeGroupName", value=node_group.nodegroup_name)
        CfnOutput(
            self, 
            "KubectlCommand",
            value=f"aws eks update-kubeconfig --name {cluster.cluster_name} --region {self.region}"
        )

app = App()

# Get environment from context, .env file, or default to staging
environment = app.node.try_get_context("environment") or os.getenv("ENVIRONMENT", "staging")

# Get AWS account and region from .env file or environment variables
account = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION", "us-east-1")

# Get stack name prefix from .env
stack_name_prefix = os.getenv("STACK_NAME_PREFIX", "EksClusterStack")

EksClusterStack(
    app, 
    f"{stack_name_prefix}-{environment}",
    environment=environment,
    env=Environment(account=account, region=region)
)

app.synth()
