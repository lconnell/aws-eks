"""VPC and networking components for AWS EKS."""

from typing import Dict, List

import pulumi_aws as aws
import pulumi_awsx as awsx

from constants import DEFAULT_EGRESS_CIDR, HTTPS_PORT
from pulumi import Output
from type_defs import VpcEndpointConfig


def create_vpc(
    name: str,
    cidr_block: str,
    availability_zones: int,
    nat_gateways: int,
    cluster_name: str,
    tags: Dict[str, str],
) -> awsx.ec2.Vpc:
    """Create a VPC with public and private subnets for EKS.

    Args:
        name: Name prefix for the VPC
        cidr_block: CIDR block for the VPC
        availability_zones: Number of availability zones
        nat_gateways: Number of NAT gateways (1 for single, or one per AZ)
        cluster_name: EKS cluster name for subnet tagging
        tags: Resource tags

    Returns:
        The created VPC
    """
    nat_strategy = (
        awsx.ec2.NatGatewayStrategy.SINGLE
        if nat_gateways == 1
        else awsx.ec2.NatGatewayStrategy.ONE_PER_AZ
    )

    return awsx.ec2.Vpc(
        name,
        cidr_block=cidr_block,
        number_of_availability_zones=availability_zones,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        subnet_strategy=awsx.ec2.SubnetAllocationStrategy.AUTO,
        nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(strategy=nat_strategy),
        subnet_specs=[
            awsx.ec2.SubnetSpecArgs(
                type=awsx.ec2.SubnetType.PUBLIC,
                tags={
                    **tags,
                    **get_alb_subnet_tags(cluster_name, "public"),
                },
            ),
            awsx.ec2.SubnetSpecArgs(
                type=awsx.ec2.SubnetType.PRIVATE,
                tags={
                    **tags,
                    **get_alb_subnet_tags(cluster_name, "private"),
                },
            ),
        ],
        tags=tags,
    )


def get_alb_subnet_tags(cluster_name: str, subnet_type: str) -> Dict[str, str]:
    """Get appropriate subnet tags for ALB discovery.

    Args:
        cluster_name: Name of the EKS cluster
        subnet_type: Type of subnet (public/private)

    Returns:
        Dictionary of tags for the subnet
    """
    tags = {f"kubernetes.io/cluster/{cluster_name}": "shared"}

    if subnet_type == "public":
        tags["kubernetes.io/role/elb"] = "1"
    elif subnet_type == "private":
        tags["kubernetes.io/role/internal-elb"] = "1"

    return tags


def create_vpc_endpoint_security_group(
    name: str,
    vpc_id: Output[str],
    vpc_cidr: str,
    tags: Dict[str, str],
    egress_cidr: str = DEFAULT_EGRESS_CIDR,
) -> aws.ec2.SecurityGroup:
    """Create a security group for VPC endpoints.

    Args:
        name: Name of the security group
        vpc_id: VPC ID
        vpc_cidr: VPC CIDR block for ingress rules
        tags: Resource tags
        egress_cidr: CIDR block for egress rules (default: 0.0.0.0/0)

    Returns:
        The created security group
    """
    return aws.ec2.SecurityGroup(
        name,
        name=name,
        description="Security group for VPC endpoints",
        vpc_id=vpc_id,
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                from_port=HTTPS_PORT,
                to_port=HTTPS_PORT,
                protocol="tcp",
                cidr_blocks=[vpc_cidr],
                description="Allow HTTPS from VPC",
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=[egress_cidr],
                description="Allow all outbound traffic",
            )
        ],
        tags=tags,
    )


def create_vpc_endpoint(config: VpcEndpointConfig) -> aws.ec2.VpcEndpoint:
    """Create VPC endpoint with consistent configuration.

    Args:
        config: VPC endpoint configuration

    Returns:
        The created VPC endpoint
    """
    name = config.get("name", "unknown")
    environment = config.get("environment", "default")
    endpoint_name = f"{name}-endpoint-{environment}"

    return aws.ec2.VpcEndpoint(
        endpoint_name,
        vpc_id=config.get("vpc_id"),
        service_name=config.get("service_name"),
        vpc_endpoint_type=config.get("endpoint_type", "Interface"),
        subnet_ids=config.get("subnet_ids"),
        security_group_ids=config.get("security_group_ids"),
        tags=config.get("tags", {}),
    )


def create_vpc_endpoints(
    vpc_id: Output[str],
    private_subnet_ids: List[Output[str]],
    security_group_id: Output[str],
    region: str,
    environment: str,
    tags: Dict[str, str],
    services: List[str],
) -> List[aws.ec2.VpcEndpoint]:
    """Create multiple VPC endpoints.

    Args:
        vpc_id: VPC ID
        private_subnet_ids: List of private subnet IDs
        security_group_id: Security group ID for interface endpoints
        region: AWS region
        environment: Environment name
        tags: Resource tags
        services: List of AWS services to create endpoints for

    Returns:
        List of created VPC endpoints
    """
    endpoints = []

    for service in services:
        if service == "s3":
            # S3 uses Gateway endpoint (free)
            endpoint = create_vpc_endpoint(
                {
                    "name": service,
                    "vpc_id": vpc_id,
                    "service_name": Output.concat(f"com.amazonaws.{region}.", service),
                    "endpoint_type": "Gateway",
                    "environment": environment,
                    "tags": tags,
                }
            )
        else:
            # Other services use Interface endpoints
            endpoint = create_vpc_endpoint(
                {
                    "name": service,
                    "vpc_id": vpc_id,
                    "service_name": Output.concat(f"com.amazonaws.{region}.", service),
                    "endpoint_type": "Interface",
                    "environment": environment,
                    "tags": tags,
                    "subnet_ids": private_subnet_ids,
                    "security_group_ids": [security_group_id],
                }
            )

        endpoints.append(endpoint)

    return endpoints
