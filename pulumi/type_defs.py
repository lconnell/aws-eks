"""Type definitions for AWS EKS infrastructure."""

from typing import Any, Dict, List, Optional, TypedDict


class TagsDict(TypedDict):
    """Standard resource tags."""

    Environment: str
    Project: str
    ManagedBy: str
    CostCenter: str


class EnvironmentConfig(TypedDict):
    """Environment-specific configuration."""

    instance_type: str
    min_size: int
    max_size: int
    desired_size: int
    nat_gateways: int
    kubernetes_version: str


class CommonConfig(TypedDict):
    """Common configuration across environments."""

    node_disk_size: int
    node_ami_type: str
    vpc_max_azs: int
    vpc_cidr: str
    enable_vpc_endpoints: bool
    enable_cluster_logging: bool
    enable_public_endpoint: bool
    enable_private_endpoint: bool
    cluster_name_prefix: str
    enable_alb_controller: bool
    enable_encryption: Optional[bool]
    kms_key_id: Optional[str]


class VpcEndpointConfig(TypedDict, total=False):
    """VPC endpoint configuration."""

    name: str
    vpc_id: Any  # Pulumi Output[str]
    service_name: Any  # Pulumi Output[str]
    endpoint_type: str
    environment: str
    tags: Dict[str, str]
    subnet_ids: Optional[List[Any]]  # Pulumi List[Output[str]]
    security_group_ids: Optional[List[Any]]  # Pulumi List[Output[str]]
