# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS EKS (Elastic Kubernetes Service) infrastructure repository using Pulumi with Python as the primary IaC tool. The project provides multi-environment EKS cluster deployments with production-ready configurations following software engineering best practices with DRY principles, helper functions, and centralized configuration management.

## Common Development Commands

All commands use Task (taskfile.dev). Run from the project root directory:

### Quick Setup
```bash
# Complete setup: install dependencies and initialize stacks
task setup
```

### Pulumi Stack Management
```bash
# Initialize a new stack
task pulumi:init env=staging
task pulumi:init env=production

# Select a stack
task pulumi:select env=staging
task pulumi:select env=production

# View stack information
task info env=staging
task status env=staging
```

### Infrastructure Management
```bash
# Preview infrastructure changes
task preview env=staging

# Deploy infrastructure changes
task deploy env=staging

# Destroy infrastructure
task destroy env=staging

# View stack outputs
task outputs env=staging

# Scale node group
task eks:scale env=staging desiredSize=3

# Configure kubectl access
task eks:kubeconfig env=staging
```

### ALB and Route 53 Management
```bash
# Check ALB and Route 53 status (coming soon)
task alb:status env=staging

# Get DNS nameserver setup instructions (coming soon)
task alb:dns:instructions env=staging

# Check Kubernetes service status
task k8s:status
```

### Development and Debugging
```bash
# View detailed stack configuration
task config env=staging

# Refresh stack state
task refresh env=staging

# Run Pulumi commands directly
task pulumi:cmd env=staging -- stack output cluster_name
task pulumi:cmd env=staging -- stack export
```

## Architecture and Key Concepts

### Infrastructure Organization
- **Multi-environment**: Uses Pulumi stacks with environment-specific configuration via .env files
- **Remote State**: Pulumi Service manages state automatically with encryption and collaboration features
- **Modern Libraries**: Uses `pulumi-aws` and `pulumi-awsx` for simplified AWS resource management
- **Code Quality**: Follows DRY principles with helper functions, centralized configuration, and type hints

### EKS Configuration Structure
- **VPC Setup**: Custom VPC with public/private subnets across 3 AZs using `awsx.ec2.Vpc`
- **Node Groups**: Managed node groups with auto-scaling (t3.medium for staging, m5.large for production)
- **Access Control**: Uses kubectl commands for cluster access after deployment (simplified approach)
- **Authentication**: Standard AWS EKS authentication via AWS CLI and kubeconfig
- **Logging**: All control plane components log to CloudWatch
- **ALB Integration**: To be implemented - AWS Application Load Balancer with flexible domain configuration
- **VPC Endpoints**: Minimal set for cost optimization (S3, EC2, STS) - $0/month for S3, ~$14.40/month for EC2+STS

### Key Files  
- `pulumi/__main__.py`: Main infrastructure definition with helper functions and centralized configuration
- `pulumi/requirements.txt`: Python dependencies for Pulumi runtime
- `pulumi/.env.example`: Environment variables template for configuration
- `pulumi/Pulumi.yaml`: Project configuration
- `pulumi/Pulumi.{staging,production}.yaml`: Stack-specific configurations
- `pulumi/README.md`: Detailed deployment documentation with best practices
- `Taskfile.yml`: Task automation definitions with Pulumi stack management
- `ALB-SETUP.md`: Detailed guide for ALB configuration (to be updated for Pulumi)

### Important Implementation Details
- Cluster version: 1.32 (configurable via `CLUSTER_VERSION` environment variable)
- Node labeling: Worker nodes automatically labeled with environment tags
- NAT Gateways: 1 for staging (cost optimization), 3 for production (high availability)
- Security: Private endpoint enabled, public endpoint configurable
- Authentication: Standard EKS authentication using AWS CLI and kubeconfig
- Access control: Admin access via `EKS_ADMIN_USER_ARN` environment variable
- VPC Endpoints: S3 (free), EC2, and STS interface endpoints for cost optimization
- Configuration: All settings managed through `.env` file with sensible defaults

### Code Quality Features
- **Helper Functions**: Reusable functions for IAM role creation and policy attachment
- **Centralized Configuration**: All settings managed through `config_vars` dictionary
- **Environment Abstraction**: Single codebase handles multiple environments
- **Type Hints**: Python type annotations for better code clarity
- **DRY Principles**: Eliminates code duplication through smart abstractions

### Before First Use
1. Ensure AWS credentials are configured
2. Copy `pulumi/.env.example` to `pulumi/.env` and update `EKS_ADMIN_USER_ARN`
3. Run quick setup: `task setup` (installs dependencies using uv and initializes stacks)
   
   Or run individual steps:
   - Install dependencies: `cd pulumi && uv pip install -r requirements.txt`
   - Initialize stacks: `task pulumi:init env=staging`
   - Configure kubectl: `task eks:kubeconfig env=staging`

### Pulumi State Management
- **Remote State**: Automatically managed by Pulumi Service with encryption
- **Collaboration**: Built-in support for team collaboration and access control
- **Versioning**: Complete history of all deployments and configuration changes
- **Rollback**: Easy rollback to previous deployments
- **No Manual Setup**: No need to manage S3 buckets or DynamoDB tables