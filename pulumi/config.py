"""Configuration management for AWS EKS infrastructure."""

from constants import (
    DEFAULT_NODE_AMI_TYPE,
    DEFAULT_NODE_DISK_SIZE,
    DEFAULT_VPC_CIDR,
    DEFAULT_VPC_MAX_AZS,
)
from pulumi import Config, get_stack
from type_defs import CommonConfig, EnvironmentConfig, TagsDict


class EKSConfig:
    """Centralized configuration management for EKS infrastructure."""

    def __init__(self) -> None:
        """Initialize configuration from Pulumi config."""
        self.config = Config("eks")
        self.environment = get_stack()

    def get_environment_config(self) -> EnvironmentConfig:
        """Get environment-specific configuration."""
        return {
            "instance_type": self._get_required("instance-type"),
            "min_size": self._get_required_int("min-size"),
            "max_size": self._get_required_int("max-size"),
            "desired_size": self._get_required_int("desired-size"),
            "nat_gateways": self._get_required_int("nat-gateways"),
            "kubernetes_version": self._get_required("kubernetes-version"),
        }

    def get_common_config(self) -> CommonConfig:
        """Get common configuration across environments."""
        return {
            "node_disk_size": (
                self.config.get_int("node-disk-size") or DEFAULT_NODE_DISK_SIZE
            ),
            "node_ami_type": self.config.get("node-ami-type") or DEFAULT_NODE_AMI_TYPE,
            "vpc_max_azs": self.config.get_int("vpc-max-azs") or DEFAULT_VPC_MAX_AZS,
            "vpc_cidr": self.config.get("vpc-cidr") or DEFAULT_VPC_CIDR,
            "enable_vpc_endpoints": (
                self.config.get_bool("enable-vpc-endpoints") or False
            ),
            "enable_cluster_logging": (
                self.config.get_bool("enable-cluster-logging") or False
            ),
            "enable_public_endpoint": (
                self.config.get_bool("enable-public-endpoint") or True
            ),
            "enable_private_endpoint": (
                self.config.get_bool("enable-private-endpoint") or False
            ),
            "cluster_name_prefix": self._get_required("cluster-name-prefix"),
            "enable_alb_controller": (
                self.config.get_bool("enable-alb-controller") or False
            ),
            "enable_encryption": self.config.get_bool("enable-encryption"),
            "kms_key_id": self.config.get("kms-key-id"),
        }

    def get_tags(self) -> TagsDict:
        """Get resource tags."""
        return {
            "Environment": self.environment,
            "Project": self._get_required("project-name"),
            "ManagedBy": self._get_required("managed-by"),
            "CostCenter": self._get_required("cost-center"),
        }

    def get_cluster_name(self) -> str:
        """Get the cluster name for the current environment."""
        prefix = self._get_required("cluster-name-prefix")
        return f"{prefix}-{self.environment}"

    def _get_required(self, key: str) -> str:
        """Get a required configuration value."""
        value = self.config.get(key)
        if not value:
            raise ValueError(f"Required configuration '{key}' is not set")
        return value

    def _get_required_int(self, key: str) -> int:
        """Get a required integer configuration value."""
        value = self.config.get_int(key)
        if value is None:
            raise ValueError(f"Required configuration '{key}' is not set")
        return value

    def validate(self) -> None:
        """Validate configuration values."""
        env_config = self.get_environment_config()
        common_config = self.get_common_config()

        # Validate node group sizing
        if env_config["min_size"] > env_config["max_size"]:
            raise ValueError("min_size cannot be greater than max_size")

        if env_config["desired_size"] < env_config["min_size"]:
            raise ValueError("desired_size cannot be less than min_size")

        if env_config["desired_size"] > env_config["max_size"]:
            raise ValueError("desired_size cannot be greater than max_size")

        # Validate NAT gateways
        if env_config["nat_gateways"] < 1:
            raise ValueError("nat_gateways must be at least 1")

        if env_config["nat_gateways"] > common_config["vpc_max_azs"]:
            raise ValueError("nat_gateways cannot exceed vpc_max_azs")

        # Validate encryption settings
        if common_config.get("kms_key_id") and not common_config.get(
            "enable_encryption"
        ):
            raise ValueError("kms_key_id requires enable_encryption to be true")
