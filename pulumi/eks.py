"""EKS Cluster deployment using Pulumi Python with environment-specific configs."""

from typing import Optional

import pulumi_aws as aws

from alb import create_alb_controller_role
from config import EKSConfig
from constants import (
    ALB_CONTROLLER_NAMESPACE,
    ALB_CONTROLLER_SERVICE_ACCOUNT,
    AWS_EC2_CONTAINER_REGISTRY_READONLY,
    AWS_EKS_CLUSTER_POLICY,
    AWS_EKS_CNI_POLICY,
    AWS_EKS_WORKER_NODE_POLICY,
    AWS_SERVICE_ENDPOINTS,
    CLUSTER_LOG_TYPES,
    OIDC_CLIENT_ID,
    OIDC_THUMBPRINT,
)
from iam import attach_policies_to_role, create_iam_role
from pulumi import Output, ResourceOptions, export
from vpc import create_vpc, create_vpc_endpoint_security_group, create_vpc_endpoints


def create_encryption_config(
    kms_key_id: Optional[str],
) -> Optional[aws.eks.ClusterEncryptionConfigArgs]:
    """Create cluster encryption configuration if enabled.

    Args:
        kms_key_id: KMS key ID for envelope encryption

    Returns:
        Encryption configuration or None if not enabled
    """
    if not kms_key_id:
        return None

    return aws.eks.ClusterEncryptionConfigArgs(
        resources=["secrets"],
        provider=aws.eks.ClusterEncryptionConfigProviderArgs(
            key_arn=kms_key_id,
        ),
    )


def create_eks_cluster() -> None:
    """Create EKS cluster with environment-specific configuration."""
    # Initialize and validate configuration
    config = EKSConfig()
    config.validate()

    # Get configuration values
    environment = config.environment
    env_config = config.get_environment_config()
    common_config = config.get_common_config()
    tags = config.get_tags()
    cluster_name = config.get_cluster_name()

    # Get current region
    current_region = aws.get_region()

    # Create VPC
    vpc = create_vpc(
        name=f"eks-vpc-{environment}",
        cidr_block=common_config["vpc_cidr"],
        availability_zones=common_config["vpc_max_azs"],
        nat_gateways=env_config["nat_gateways"],
        cluster_name=cluster_name,
        tags=tags,
    )

    # Create IAM roles
    cluster_role = create_iam_role(
        f"eks-cluster-role-{environment}",
        "eks.amazonaws.com",
        tags,
    )

    node_role = create_iam_role(
        f"eks-node-role-{environment}",
        "ec2.amazonaws.com",
        tags,
    )

    # Attach cluster policy
    cluster_policy_attachment = aws.iam.RolePolicyAttachment(
        f"eks-cluster-policy-{environment}",
        role=cluster_role.name,
        policy_arn=AWS_EKS_CLUSTER_POLICY,
    )

    # Attach node policies
    node_policies = [
        AWS_EKS_WORKER_NODE_POLICY,
        AWS_EKS_CNI_POLICY,
        AWS_EC2_CONTAINER_REGISTRY_READONLY,
    ]

    node_policy_attachments = attach_policies_to_role(
        node_role,
        node_policies,
        f"eks-node-{environment}",
    )

    # Configure endpoint access
    endpoint_config = {
        "private_access": common_config["enable_private_endpoint"],
        "public_access": (
            common_config["enable_public_endpoint"]
            if common_config["enable_private_endpoint"]
            else True
        ),
    }

    # Configure cluster logging
    cluster_logging_types = (
        CLUSTER_LOG_TYPES if common_config["enable_cluster_logging"] else []
    )

    # Configure encryption
    encryption_config = None
    if common_config.get("enable_encryption") and common_config.get("kms_key_id"):
        encryption_config = create_encryption_config(common_config["kms_key_id"])

    # Create EKS cluster
    cluster = aws.eks.Cluster(
        f"eks-cluster-{environment}",
        name=cluster_name,
        role_arn=cluster_role.arn,
        vpc_config=aws.eks.ClusterVpcConfigArgs(
            subnet_ids=vpc.private_subnet_ids,
            endpoint_private_access=endpoint_config["private_access"],
            endpoint_public_access=endpoint_config["public_access"],
        ),
        version=env_config["kubernetes_version"],
        enabled_cluster_log_types=cluster_logging_types,
        encryption_config=encryption_config,
        tags=tags,
        opts=ResourceOptions(depends_on=[cluster_policy_attachment]),
    )

    # Create OIDC provider for the cluster (required for IRSA)
    oidc_provider = aws.iam.OpenIdConnectProvider(
        f"eks-oidc-provider-{environment}",
        url=cluster.identities[0].oidcs[0].issuer,
        client_id_lists=[OIDC_CLIENT_ID],
        thumbprint_lists=[OIDC_THUMBPRINT],
        tags=tags,
    )

    # Create EKS node group
    node_group = aws.eks.NodeGroup(
        f"eks-nodegroup-{environment}",
        cluster_name=cluster.name,
        node_group_name=f"eks-nodegroup-{environment}",
        node_role_arn=node_role.arn,
        subnet_ids=vpc.private_subnet_ids,
        instance_types=[env_config["instance_type"]],
        ami_type=common_config["node_ami_type"],
        disk_size=common_config["node_disk_size"],
        scaling_config=aws.eks.NodeGroupScalingConfigArgs(
            desired_size=env_config["desired_size"],
            max_size=env_config["max_size"],
            min_size=env_config["min_size"],
        ),
        labels=tags,
        tags=tags,
        opts=ResourceOptions(depends_on=node_policy_attachments),
    )

    # Create ALB Controller prerequisites if enabled
    alb_controller_role_arn = None
    if common_config["enable_alb_controller"]:
        # Create IRSA role for ALB Controller
        _, alb_controller_role_arn = create_alb_controller_role(
            environment=environment,
            oidc_issuer=cluster.identities[0].oidcs[0].issuer,
            oidc_provider_arn=oidc_provider.arn,
            tags=tags,
        )

    # Add VPC endpoints for cost optimization (if enabled)
    if common_config["enable_vpc_endpoints"]:
        # Create a security group for VPC endpoints
        endpoint_sg = create_vpc_endpoint_security_group(
            name=f"vpc-endpoint-sg-{environment}",
            vpc_id=vpc.vpc_id,
            vpc_cidr=common_config["vpc_cidr"],
            tags=tags,
        )

        # Create VPC endpoints
        create_vpc_endpoints(
            vpc_id=vpc.vpc_id,
            private_subnet_ids=vpc.private_subnet_ids,
            security_group_id=endpoint_sg.id,
            region=current_region.name,
            environment=environment,
            tags=tags,
            services=AWS_SERVICE_ENDPOINTS,
        )

    # Export important values
    export("cluster_name", cluster.name)
    export("cluster_endpoint", cluster.endpoint)
    export("cluster_arn", cluster.arn)
    export("cluster_version", cluster.version)
    export("vpc_id", vpc.vpc_id)
    export("node_group_name", node_group.node_group_name)
    export("oidc_provider_arn", oidc_provider.arn)
    export("oidc_issuer", cluster.identities[0].oidcs[0].issuer)
    export("public_subnet_ids", vpc.public_subnet_ids)
    export("private_subnet_ids", vpc.private_subnet_ids)
    export(
        "kubectl_command",
        Output.concat(
            "aws eks update-kubeconfig --name ",
            cluster.name,
            " --region ",
            current_region.name,
        ),
    )

    # Export ALB Controller specific values if enabled
    if common_config["enable_alb_controller"]:
        export("alb_controller_role_arn", alb_controller_role_arn)
        export(
            "alb_controller_service_account",
            f"system:serviceaccount:{ALB_CONTROLLER_NAMESPACE}:{ALB_CONTROLLER_SERVICE_ACCOUNT}",
        )
