# General Variables
variable "aws_region" {
  description = "AWS region for the EKS cluster"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g., staging, production)"
  type        = string
}

variable "cluster_base_name" {
  description = "Base name for the EKS cluster (e.g., 'ai-agents', 'web-app'). Environment will be appended."
  type        = string
  default     = "my-eks"
}

# EKS Cluster Variables
variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.32"
}

variable "eks_admin_user_arn" {
  description = "IAM ARN of the user to be granted EKS cluster admin access via access entries."
  type        = string
  default     = "" # Should be overridden in .tfvars
}

variable "additional_access_entries" {
  description = "Map of additional EKS access entries for IAM principals"
  type = map(object({
    principal_arn = string
    user_name     = optional(string)
    type          = optional(string, "STANDARD")
    policy_associations = optional(map(object({
      policy_arn = string
      access_scope = object({
        type       = string
        namespaces = optional(list(string))
      })
    })), {})
  }))
  default = {}
}

variable "vpc_name" {
  description = "Name for the VPC"
  type        = string
  default     = "my-eks-vpc"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of Availability Zones to use for the VPC and subnets"
  type        = list(string)
  # Example: ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "num_nat_gateways" {
  description = "Number of NAT gateways to create. Set to 0 for no NAT gateways (e.g., for public subnets only or if using VPC endpoints). For production, typically 1 per AZ or at least 1."
  type        = number
  default     = 1
}

# Managed Node Group Variables
variable "managed_node_group_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "managed_node_group_min_size" {
  description = "Minimum number of nodes in the managed node group"
  type        = number
  default     = 2
}

variable "managed_node_group_max_size" {
  description = "Maximum number of nodes in the managed node group"
  type        = number
  default     = 3
}

variable "managed_node_group_desired_size" {
  description = "Desired number of nodes in the managed node group"
  type        = number
  default     = 2
}

# Tags
variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}
