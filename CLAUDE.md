# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS EKS (Elastic Kubernetes Service) infrastructure repository using Terraform as the primary IaC tool, with an alternative CDK implementation. The project provides multi-environment EKS cluster deployments with production-ready configurations.

## Common Development Commands

All commands use Task (taskfile.dev). Run from the project root directory:

### Quick Setup
```bash
# Complete setup: create backend, initialize, and create workspaces
task setup
```

### S3 Backend Management
```bash
# Create S3 bucket for Terraform state
task backend:create

# Initialize Terraform with S3 backend
task backend:init

# Show S3 bucket information
task backend:info

# Initialize workspaces
task terraform:workspace:init

# Select workspace
task terraform:workspace:select env=staging
task terraform:workspace:select env=production
```

### Infrastructure Management
```bash
# Plan infrastructure changes (or use shorter alias)
task terraform:plan env=staging
task plan env=staging

# Apply infrastructure changes (or use shorter alias)
task terraform:apply env=staging
task apply env=staging

# Destroy infrastructure (or use shorter alias)
task terraform:destroy env=staging
task destroy env=staging

# Scale node group
task eks:scale desiredSize=3

# Configure kubectl access
task eks:kubeconfig

# Switch kubectl context
task eks:kubectx
```

### ALB and Route 53 Management
```bash
# Check ALB and Route 53 status
task alb:status

# Get DNS nameserver setup instructions (for custom domains)
task alb:dns:instructions

# Check Kubernetes service status
task k8s:status
```

### Terraform Validation and Formatting
```bash
# Validate Terraform configuration
task terraform:validate

# Format Terraform files
task terraform:format

# Check if files are properly formatted
task terraform:format:check
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
- **Access Control**: Modern EKS Access Entries API for IAM-based authentication (replaces deprecated aws-auth ConfigMap)
- **Authentication Mode**: API_AND_CONFIG_MAP mode for both access entries and node group compatibility
- **Logging**: All control plane components log to CloudWatch
- **ALB Integration**: AWS Application Load Balancer with flexible domain configuration (default AWS domain or custom domain with Route 53)

### Key Files
- `terraform/eks.tf`: Main cluster configuration using terraform-aws-modules with EKS Access Entries
- `terraform/alb.tf`: Complete ALB, Route 53, and SSL certificate configuration with flexible domain support
- `terraform/variables.tf`: All configurable parameters with defaults and access entry definitions
- `terraform/{staging,production}.tfvars`: Environment-specific values including ALB configuration
- `terraform/access-entries-example.tfvars`: Example configuration for additional IAM access entries
- `terraform/standalone-access-entry-example.tf`: Reference for direct aws_eks_access_entry resource usage
- `Taskfile.yml`: Task automation definitions with workspace-aware commands (at project root)
- `terraform/backend.tf`: S3 backend configuration for state storage
- `terraform-backend/s3-backend.tf`: Separate Terraform configuration for creating the S3 state bucket
- `ALB-SETUP.md`: Detailed guide for ALB configuration and subdomain routing setup

### Important Implementation Details
- Cluster version: 1.33 (configurable via `cluster_version` variable)
- Node labeling: Worker nodes automatically labeled with `node-role.kubernetes.io/worker`
- NAT Gateways: 1 for staging (cost optimization), 3 for production (high availability)
- Security: Private endpoint enabled, public endpoint configurable
- Authentication: API_AND_CONFIG_MAP mode with EKS Access Entries (supports both modern access entries and aws-auth ConfigMap for node groups)
- Access control: Admin access via `eks_admin_user_arn`, additional entries via `additional_access_entries`
- Available AWS EKS policies: AmazonEKSClusterAdminPolicy, AmazonEKSEditPolicy, AmazonEKSViewPolicy
- ALB Configuration: Two modes available - default AWS domain (subdomain routing) or custom domain with SSL and Route 53
- ALB Routing: Subdomain-based routing for both modes (api.domain.com, argocd.domain.com)

### Before First Use
1. Ensure AWS credentials are configured
2. Set the `eks_admin_user_arn` variable to your IAM user for admin access
3. Run quick setup: `task setup` (creates backend, initializes, and creates workspaces)
   
   Or run individual steps:
   - Create S3 bucket for Terraform state: `task backend:create`
   - Initialize backend: `task backend:init`
   - Initialize workspaces: `task terraform:workspace:init`

### S3 Backend Features
- **Versioning**: Enabled for state file history
- **Lifecycle Policy**: Retains 2 newest noncurrent versions, older versions deleted after 90 days
- **Encryption**: Server-side encryption with AES256
- **Naming**: Default format is `{account-id}-eks-terraform-state`