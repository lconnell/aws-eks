"""ALB Controller configuration for EKS clusters."""

from typing import Dict, Tuple

import pulumi_aws as aws

from constants import (
    ALB_CONTROLLER_NAMESPACE,
    ALB_CONTROLLER_SERVICE_ACCOUNT,
    AWS_ELB_FULL_ACCESS,
)
from iam import create_irsa_role
from pulumi import Output


def create_alb_controller_role(
    environment: str,
    oidc_issuer: Output[str],
    oidc_provider_arn: Output[str],
    tags: Dict[str, str],
) -> Tuple[aws.iam.Role, Output[str]]:
    """Create IRSA role for AWS Load Balancer Controller.

    Args:
        environment: Environment name (staging/production)
        oidc_issuer: OIDC issuer URL from EKS cluster
        oidc_provider_arn: OIDC provider ARN
        tags: Resource tags

    Returns:
        Tuple of (IAM Role, Role ARN)
    """
    role = create_irsa_role(
        name=f"eks-alb-controller-role-{environment}",
        oidc_issuer=oidc_issuer,
        oidc_provider_arn=oidc_provider_arn,
        namespace=ALB_CONTROLLER_NAMESPACE,
        service_account=ALB_CONTROLLER_SERVICE_ACCOUNT,
        policy_arns=[AWS_ELB_FULL_ACCESS],
        tags=tags,
    )

    return role, role.arn
