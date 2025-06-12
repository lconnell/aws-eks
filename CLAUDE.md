# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS EKS (Elastic Kubernetes Service) infrastructure repository using Terraform as the primary IaC tool, with an alternative CDK implementation. The project provides multi-environment EKS cluster deployments with production-ready configurations.

## Common Development Commands

All commands use Task (taskfile.dev). Run from the `terraform/` directory:

### S3 Backend Management
```bash
# Create S3 bucket for Terraform state
task backend:create

# Initialize Terraform with S3 backend
task backend:init

# Show S3 bucket information
task backend:info

# Initialize workspaces
task workspace:init

# Select workspace
task workspace:select env=staging
task workspace:select env=production
```

### Infrastructure Management
```bash
# Plan infrastructure changes
task plan env=staging
task plan env=production

# Apply infrastructure changes
task apply env=staging
task apply env=production

# Destroy infrastructure
task destroy env=staging
task destroy env=production

# Scale node group
task scale desiredSize=3

# Configure kubectl access
task kubeconfig

# Switch kubectl context
task kubectx
```

## Architecture and Key Concepts

### Infrastructure Organization
- **Multi-environment**: Uses Terraform workspaces with separate tfvars files (staging.tfvars, production.tfvars)
- **Remote State**: S3 backend with native state locking - managed through dedicated Terraform configuration
- **Module-based**: Uses official terraform-aws-modules for VPC and EKS
- **Backend Isolation**: S3 bucket for state storage is managed separately in `terraform-backend/` to avoid circular dependencies

### EKS Configuration Structure
- **VPC Setup**: Custom VPC with public/private subnets across 3 AZs
- **Node Groups**: Managed node groups with auto-scaling (t3.medium for staging, m5.large for production)
- **Access Control**: Modern EKS Access Entries for IAM-based authentication (not deprecated aws-auth ConfigMap)
- **Logging**: All control plane components log to CloudWatch

### Key Files
- `terraform/eks.tf`: Main cluster configuration using terraform-aws-modules
- `terraform/variables.tf`: All configurable parameters with defaults
- `terraform/{staging,production}.tfvars`: Environment-specific values
- `terraform/Taskfile.yml`: Task automation definitions with workspace-aware commands
- `terraform/backend.tf`: S3 backend configuration for state storage
- `terraform-backend/s3-backend.tf`: Separate Terraform configuration for creating the S3 state bucket

### Important Implementation Details
- Cluster version: 1.32 (configurable via `cluster_version` variable)
- Node labeling: Worker nodes automatically labeled with `node-role.kubernetes.io/worker`
- NAT Gateways: 1 for staging (cost optimization), 3 for production (high availability)
- Security: Private endpoint enabled, public endpoint configurable
- Cluster admin access granted via `cluster_admin_iam_user` variable

### Before First Use
1. Create S3 bucket for Terraform state: `task backend:create`
2. Initialize backend: `task backend:init`
3. Initialize workspaces: `task workspace:init`
4. Ensure AWS credentials are configured
5. Set the `cluster_admin_iam_user` variable to your IAM user for admin access

### S3 Backend Features
- **Versioning**: Enabled for state file history
- **Lifecycle Policy**: Retains 2 newest noncurrent versions, older versions deleted after 90 days
- **Encryption**: Server-side encryption with AES256
- **Naming**: Default format is `{account-id}-eks-terraform-state`