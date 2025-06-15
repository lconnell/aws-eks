"""
EKS Cluster deployment using Pulumi Python with environment-specific configurations
"""

import os
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def create_iam_role(name: str, service: str, tags: dict):
    """Create IAM role with assume role policy for specified service"""
    return aws.iam.Role(
        name,
        assume_role_policy=f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Principal": {{
                        "Service": "{service}"
                    }},
                    "Action": "sts:AssumeRole"
                }}
            ]
        }}""",
        tags=tags
    )

def attach_policies_to_role(role_name: str, policy_arns: list, environment: str):
    """Attach multiple policies to an IAM role"""
    attachments = []
    for i, policy_arn in enumerate(policy_arns):
        attachment = aws.iam.RolePolicyAttachment(
            f"{role_name}-policy-{i}-{environment}",
            role=role_name,
            policy_arn=policy_arn
        )
        attachments.append(attachment)
    return attachments

def create_eks_cluster():
    """Create EKS cluster with environment-specific configuration"""
    
    # Get environment configuration
    environment = os.getenv("ENVIRONMENT", "staging")
    
    # Environment-specific configuration
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
    
    # Common configuration
    config_vars = {
        "node_disk_size": int(os.getenv("NODE_DISK_SIZE", "100")),
        "node_ami_type": os.getenv("NODE_AMI_TYPE", "AL2_x86_64"),
        "vpc_max_azs": int(os.getenv("VPC_MAX_AZS", "3")),
        "vpc_cidr": os.getenv("VPC_CIDR", "10.0.0.0/16"),
        "enable_vpc_endpoints": os.getenv("ENABLE_VPC_ENDPOINTS", "true").lower() == "true",
        "enable_cluster_logging": os.getenv("ENABLE_CLUSTER_LOGGING", "true").lower() == "true",
        "enable_public_endpoint": os.getenv("ENABLE_PUBLIC_ENDPOINT", "true").lower() == "true",
        "enable_private_endpoint": os.getenv("ENABLE_PRIVATE_ENDPOINT", "true").lower() == "true",
        "cluster_name_prefix": os.getenv("CLUSTER_NAME_PREFIX", "eks-cluster"),
    }
    
    # Tag configuration
    tags = {
        "Environment": environment,
        "Project": os.getenv("TAG_PROJECT", "EKS-Pulumi"),
        "ManagedBy": os.getenv("TAG_MANAGED_BY", "Pulumi"),
        "CostCenter": os.getenv("TAG_COST_CENTER", "engineering")
    }
    
    # Create VPC with environment-specific settings
    vpc = awsx.ec2.Vpc(
        f"eks-vpc-{environment}",
        cidr_block=config_vars["vpc_cidr"],
        number_of_availability_zones=config_vars["vpc_max_azs"],
        enable_dns_hostnames=True,
        enable_dns_support=True,
        nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
            strategy=awsx.ec2.NatGatewayStrategy.SINGLE if env_config["nat_gateways"] == 1 
                    else awsx.ec2.NatGatewayStrategy.ONE_PER_AZ
        ),
        tags=tags
    )
    
    # Create IAM roles using helper functions
    cluster_role = create_iam_role(f"eks-cluster-role-{environment}", "eks.amazonaws.com", tags)
    node_role = create_iam_role(f"eks-node-role-{environment}", "ec2.amazonaws.com", tags)
    
    # Attach cluster policy
    cluster_policy_attachment = aws.iam.RolePolicyAttachment(
        f"eks-cluster-policy-{environment}",
        role=cluster_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
    )
    
    # Attach node policies
    node_policies = [
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    ]
    
    node_policy_attachments = []
    for i, policy_arn in enumerate(node_policies):
        attachment = aws.iam.RolePolicyAttachment(
            f"eks-node-policy-{i}-{environment}",
            role=node_role.name,
            policy_arn=policy_arn
        )
        node_policy_attachments.append(attachment)
    
    # Configure endpoint access
    endpoint_config = {
        "private_access": config_vars["enable_private_endpoint"],
        "public_access": config_vars["enable_public_endpoint"] if config_vars["enable_private_endpoint"] else True
    }
    
    # Configure cluster logging
    cluster_logging_types = [
        "api", "audit", "authenticator", "controllerManager", "scheduler"
    ] if config_vars["enable_cluster_logging"] else []
    
    # Create EKS cluster
    cluster = aws.eks.Cluster(
        f"eks-cluster-{environment}",
        name=f"{config_vars['cluster_name_prefix']}-{environment}",
        role_arn=cluster_role.arn,
        vpc_config=aws.eks.ClusterVpcConfigArgs(
            subnet_ids=vpc.private_subnet_ids,
            endpoint_private_access=endpoint_config["private_access"],
            endpoint_public_access=endpoint_config["public_access"],
        ),
        version="1.32",
        enabled_cluster_log_types=cluster_logging_types,
        tags=tags,
        opts=pulumi.ResourceOptions(depends_on=[cluster_policy_attachment])
    )
    
    # Create EKS node group
    node_group = aws.eks.NodeGroup(
        f"eks-nodegroup-{environment}",
        cluster_name=cluster.name,
        node_group_name=f"eks-nodegroup-{environment}",
        node_role_arn=node_role.arn,
        subnet_ids=vpc.private_subnet_ids,
        instance_types=[env_config["instance_type"]],
        ami_type=config_vars["node_ami_type"],
        disk_size=config_vars["node_disk_size"],
        scaling_config=aws.eks.NodeGroupScalingConfigArgs(
            desired_size=env_config["desired_size"],
            max_size=env_config["max_size"],
            min_size=env_config["min_size"]
        ),
        labels=tags,
        tags=tags,
        opts=pulumi.ResourceOptions(depends_on=node_policy_attachments)
    )
    
    # Add VPC endpoints for cost optimization (if enabled)
    if config_vars["enable_vpc_endpoints"]:
        # Get current region
        current_region = aws.get_region()
        
        # Create a security group for VPC endpoints
        endpoint_sg = aws.ec2.SecurityGroup(
            f"vpc-endpoint-sg-{environment}",
            name=f"vpc-endpoint-sg-{environment}",
            description="Security group for VPC endpoints",
            vpc_id=vpc.vpc_id,
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    from_port=443,
                    to_port=443,
                    protocol="tcp",
                    cidr_blocks=[config_vars["vpc_cidr"]]
                )
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            tags=tags
        )
        
        # S3 Gateway Endpoint (free)
        # Note: Gateway endpoints automatically associate with all route tables
        aws.ec2.VpcEndpoint(
            f"s3-endpoint-{environment}",
            vpc_id=vpc.vpc_id,
            service_name=f"com.amazonaws.{current_region.name}.s3",
            vpc_endpoint_type="Gateway",
            tags=tags
        )
        
        # EC2 Interface Endpoint
        aws.ec2.VpcEndpoint(
            f"ec2-endpoint-{environment}",
            vpc_id=vpc.vpc_id,
            service_name=f"com.amazonaws.{current_region.name}.ec2",
            vpc_endpoint_type="Interface",
            subnet_ids=vpc.private_subnet_ids,
            security_group_ids=[endpoint_sg.id],
            tags=tags
        )
        
        # STS Interface Endpoint
        aws.ec2.VpcEndpoint(
            f"sts-endpoint-{environment}",
            vpc_id=vpc.vpc_id,
            service_name=f"com.amazonaws.{current_region.name}.sts",
            vpc_endpoint_type="Interface",
            subnet_ids=vpc.private_subnet_ids,
            security_group_ids=[endpoint_sg.id],
            tags=tags
        )
    
    # Export important values
    pulumi.export("cluster_name", cluster.name)
    pulumi.export("cluster_endpoint", cluster.endpoint)
    pulumi.export("cluster_arn", cluster.arn)
    pulumi.export("vpc_id", vpc.vpc_id)
    pulumi.export("node_group_name", node_group.node_group_name)
    pulumi.export("kubectl_command", pulumi.Output.concat(
        "aws eks update-kubeconfig --name ", cluster.name, 
        " --region ", aws.get_region().name
    ))

if __name__ == "__main__":
    create_eks_cluster()