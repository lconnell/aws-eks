terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Using a recent version, adjust if needed
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20" # Ensure compatibility with your K8s version
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10" # Ensure compatibility
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  required_version = ">= 1.3"
}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0" # Use a recent, stable version

  name = "${var.vpc_name}-${var.environment}"
  cidr = var.vpc_cidr_block

  azs             = var.availability_zones
  private_subnets = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr_block, 8, k)] # Example: creates /24 subnets
  public_subnets  = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr_block, 8, k + length(var.availability_zones))] # Example: creates /24 subnets

  enable_nat_gateway = var.num_nat_gateways > 0
  single_nat_gateway = var.num_nat_gateways == 1
  one_nat_gateway_per_az = var.num_nat_gateways > 1 && var.num_nat_gateways == length(var.availability_zones)
  # If num_nat_gateways is > 1 but not equal to length(var.availability_zones), the module will create `num_nat_gateways` across the AZs.

  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = merge(
    var.tags,
    { "Name" = "${var.vpc_name}-${var.environment}" }
  )
}

#------------------------------------------------------------------------------
# EKS Cluster
#------------------------------------------------------------------------------
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = var.tags
  }
}

locals {
  cluster_name = "${var.cluster_base_name}-${var.environment}"
  # Extract the username/role name from the ARN
  # Example ARN: arn:aws:iam::123456789012:user/devsecops
  # Or for a role: arn:aws:iam::123456789012:role/path/to/RoleName
  # This regex attempts to capture 'devsecops' or 'RoleName'
  admin_principal_name = regex("^arn:aws:iam::[0-9]+:(?:user|role)/(?:.*/)?([^/]+)$", var.eks_admin_user_arn)[0]
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0" # Using a recent version of the EKS module

  cluster_name    = local.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets # EKS worker nodes typically go into private subnets
  control_plane_subnet_ids = module.vpc.private_subnets # For EKS >= 1.20, control plane can be in private subnets

  # Endpoint access configuration
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = false
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

  # aws-auth configmap management
  access_entries = {
    # Use the extracted name for the access entry key for clarity
    "${local.admin_principal_name}_admin" = {
      principal_arn     = var.eks_admin_user_arn
      user_name         = local.admin_principal_name
      policy_associations = {
        cluster_admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  # Enable CloudWatch Container Logs
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Managed Node Group
  eks_managed_node_groups = {
    main = {
      name           = "${local.cluster_name}-mng"
      instance_types = var.managed_node_group_instance_types
      min_size       = var.managed_node_group_min_size
      max_size       = var.managed_node_group_max_size
      labels = {
        "node-role.kubernetes.io/worker" = "worker"
      }
      desired_size   = var.managed_node_group_desired_size

      # Ensure nodes are launched in the specified subnets
      subnet_ids = module.vpc.private_subnets # Place worker nodes in private subnets

      tags = merge(
        var.tags,
        {
          Name = "${local.cluster_name}-mng"
          "eks_cluster_name"                                = local.cluster_name
          "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
          "k8s.io/cluster-autoscaler/enabled"               = "true"
        }
      )
    }
  }

  # Cluster access (optional, for granting access to other IAM roles/users)
  # manage_aws_auth_configmap = true
  # aws_auth_roles = [
  #   {
  #     rolearn  = "arn:aws:iam::ACCOUNT_ID:role/YourAdminRole"
  #     username = "admin-role"
  #     groups   = ["system:masters"]
  #   },
  # ]
  # aws_auth_users = [
  #   {
  #     userarn  = "arn:aws:iam::ACCOUNT_ID:user/YourUser"
  #     username = "your-user"
  #     groups   = ["system:masters"]
  #   },
  # ]

  tags = var.tags
}
