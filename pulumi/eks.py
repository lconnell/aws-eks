"""
EKS Cluster deployment using Pulumi Python with environment-specific configurations
"""

import pulumi_aws as aws
import pulumi_awsx as awsx

from pulumi import Config, Output, ResourceOptions, export, get_stack


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
        tags=tags,
    )


def attach_policies_to_role(role: aws.iam.Role, policy_arns: list, prefix: str):
    """Attach multiple policies to an IAM role"""
    attachments = []
    for i, policy_arn in enumerate(policy_arns):
        attachment = aws.iam.RolePolicyAttachment(
            f"{prefix}-policy-{i}", role=role.name, policy_arn=policy_arn
        )
        attachments.append(attachment)
    return attachments


def create_vpc_endpoint(
    name: str,
    vpc_id: str,
    service_name: str,
    endpoint_type: str,
    environment: str,
    tags: dict,
    subnet_ids=None,
    security_group_ids=None,
):
    """Create VPC endpoint with consistent configuration"""
    return aws.ec2.VpcEndpoint(
        f"{name}-endpoint-{environment}",
        vpc_id=vpc_id,
        service_name=service_name,
        vpc_endpoint_type=endpoint_type,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        tags=tags,
    )


def create_eks_cluster():
    """Create EKS cluster with environment-specific configuration"""

    # Initialize Pulumi configuration
    config = Config("eks")

    # Get stack name as environment (staging/production)
    environment = get_stack()

    # Environment-specific configuration with Pulumi config
    env_config = {
        "instance_type": config.get("instance-type"),
        "min_size": config.get_int("min-size"),
        "max_size": config.get_int("max-size"),
        "desired_size": config.get_int("desired-size"),
        "nat_gateways": config.get_int("nat-gateways"),
        "kubernetes_version": config.get("kubernetes-version"),
    }

    # Common configuration using Pulumi config
    config_vars = {
        "node_disk_size": config.get_int("node-disk-size"),
        "node_ami_type": config.get("node-ami-type"),
        "vpc_max_azs": config.get_int("vpc-max-azs"),
        "vpc_cidr": config.get("vpc-cidr"),
        "enable_vpc_endpoints": config.get_bool("enable-vpc-endpoints"),
        "enable_cluster_logging": config.get_bool("enable-cluster-logging"),
        "enable_public_endpoint": config.get_bool("enable-public-endpoint"),
        "enable_private_endpoint": config.get_bool("enable-private-endpoint"),
        "cluster_name_prefix": config.get("cluster-name-prefix"),
    }

    # Tag configuration using Pulumi config
    tags = {
        "Environment": environment,
        "Project": config.get("project-name"),
        "ManagedBy": config.get("managed-by"),
        "CostCenter": config.get("cost-center"),
    }

    # Create VPC with environment-specific settings
    vpc = awsx.ec2.Vpc(
        f"eks-vpc-{environment}",
        cidr_block=config_vars["vpc_cidr"],
        number_of_availability_zones=config_vars["vpc_max_azs"],
        enable_dns_hostnames=True,
        enable_dns_support=True,
        nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
            strategy=awsx.ec2.NatGatewayStrategy.SINGLE
            if env_config["nat_gateways"] == 1
            else awsx.ec2.NatGatewayStrategy.ONE_PER_AZ
        ),
        tags=tags,
    )

    # Create IAM roles using helper functions
    cluster_role = create_iam_role(
        f"eks-cluster-role-{environment}", "eks.amazonaws.com", tags
    )
    node_role = create_iam_role(
        f"eks-node-role-{environment}", "ec2.amazonaws.com", tags
    )

    # Attach cluster policy
    cluster_policy_attachment = aws.iam.RolePolicyAttachment(
        f"eks-cluster-policy-{environment}",
        role=cluster_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    )

    # Attach node policies using helper function
    node_policies = [
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    ]

    node_policy_attachments = attach_policies_to_role(
        node_role, node_policies, f"eks-node-{environment}"
    )

    # Configure endpoint access
    endpoint_config = {
        "private_access": config_vars["enable_private_endpoint"],
        "public_access": config_vars["enable_public_endpoint"]
        if config_vars["enable_private_endpoint"]
        else True,
    }

    # Configure cluster logging
    cluster_logging_types = (
        ["api", "audit", "authenticator", "controllerManager", "scheduler"]
        if config_vars["enable_cluster_logging"]
        else []
    )

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
        version=env_config["kubernetes_version"],
        enabled_cluster_log_types=cluster_logging_types,
        tags=tags,
        opts=ResourceOptions(depends_on=[cluster_policy_attachment]),
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
            min_size=env_config["min_size"],
        ),
        labels=tags,
        tags=tags,
        opts=ResourceOptions(depends_on=node_policy_attachments),
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
                    cidr_blocks=[config_vars["vpc_cidr"]],
                )
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"]
                )
            ],
            tags=tags,
        )

        # S3 Gateway Endpoint (free)
        # Note: Gateway endpoints automatically associate with all route tables
        create_vpc_endpoint(
            "s3",
            vpc.vpc_id,
            Output.concat("com.amazonaws.", current_region.name, ".s3"),
            "Gateway",
            environment,
            tags,
        )

        # Interface endpoints for EC2 and STS
        for service in ["ec2", "sts"]:
            create_vpc_endpoint(
                service,
                vpc.vpc_id,
                Output.concat("com.amazonaws.", current_region.name, f".{service}"),
                "Interface",
                environment,
                tags,
                subnet_ids=vpc.private_subnet_ids,
                security_group_ids=[endpoint_sg.id],
            )

    # Export important values
    export("cluster_name", cluster.name)
    export("cluster_endpoint", cluster.endpoint)
    export("cluster_arn", cluster.arn)
    export("cluster_version", cluster.version)
    export("vpc_id", vpc.vpc_id)
    export("node_group_name", node_group.node_group_name)
    export(
        "kubectl_command",
        Output.concat(
            "aws eks update-kubeconfig --name ",
            cluster.name,
            " --region ",
            aws.get_region().name,
        ),
    )


if __name__ == "__main__":
    create_eks_cluster()
