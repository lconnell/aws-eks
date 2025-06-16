"""IAM role and policy management for AWS EKS."""

import json
from typing import Dict, List

import pulumi_aws as aws

from constants import OIDC_CLIENT_ID
from pulumi import Output


def create_iam_role(name: str, service: str, tags: Dict[str, str]) -> aws.iam.Role:
    """Create IAM role with assume role policy for specified service.

    Args:
        name: Name of the IAM role
        service: AWS service that can assume this role (e.g., 'eks.amazonaws.com')
        tags: Resource tags

    Returns:
        The created IAM role
    """
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": service},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    return aws.iam.Role(
        name,
        assume_role_policy=json.dumps(assume_role_policy),
        tags=tags,
    )


def attach_policies_to_role(
    role: aws.iam.Role,
    policy_arns: List[str],
    prefix: str,
) -> List[aws.iam.RolePolicyAttachment]:
    """Attach multiple policies to an IAM role.

    Args:
        role: The IAM role to attach policies to
        policy_arns: List of policy ARNs to attach
        prefix: Prefix for resource names

    Returns:
        List of policy attachments
    """
    attachments = []
    for i, policy_arn in enumerate(policy_arns):
        attachment = aws.iam.RolePolicyAttachment(
            f"{prefix}-policy-{i}",
            role=role.name,
            policy_arn=policy_arn,
        )
        attachments.append(attachment)
    return attachments


def create_irsa_assume_role_policy(
    oidc_issuer: Output[str],
    oidc_provider_arn: Output[str],
    namespace: str,
    service_account: str,
) -> Output[str]:
    """Create an assume role policy for IRSA (IAM Roles for Service Accounts).

    Args:
        oidc_issuer: OIDC issuer URL from EKS cluster
        oidc_provider_arn: OIDC provider ARN
        namespace: Kubernetes namespace
        service_account: Kubernetes service account name

    Returns:
        JSON assume role policy as Output[str]
    """
    return Output.all(oidc_issuer, oidc_provider_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Federated": args[1]},
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringEquals": {
                                f"{args[0].replace('https://', '')}:sub": (
                                    f"system:serviceaccount:{namespace}:{service_account}"
                                ),
                                f"{args[0].replace('https://', '')}:aud": (
                                    OIDC_CLIENT_ID
                                ),
                            }
                        },
                    }
                ],
            }
        )
    )


def create_irsa_role(
    name: str,
    oidc_issuer: Output[str],
    oidc_provider_arn: Output[str],
    namespace: str,
    service_account: str,
    policy_arns: List[str],
    tags: Dict[str, str],
) -> aws.iam.Role:
    """Create an IAM role for a Kubernetes service account (IRSA).

    Args:
        name: Name of the IAM role
        oidc_issuer: OIDC issuer URL from EKS cluster
        oidc_provider_arn: OIDC provider ARN
        namespace: Kubernetes namespace
        service_account: Kubernetes service account name
        policy_arns: List of policy ARNs to attach
        tags: Resource tags

    Returns:
        The created IAM role with attached policies
    """
    assume_role_policy = create_irsa_assume_role_policy(
        oidc_issuer,
        oidc_provider_arn,
        namespace,
        service_account,
    )

    role = aws.iam.Role(
        name,
        assume_role_policy=assume_role_policy,
        tags=tags,
    )

    # Attach policies
    attach_policies_to_role(role, policy_arns, name)

    return role
