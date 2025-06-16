# CLAUDE.md

This file provides guidance to me, Cascade, when working with code in this repository.

## Project Overview

This is an AWS EKS (Elastic Kubernetes Service) infrastructure repository using Pulumi with Python as the primary IaC tool. The project provides multi-environment EKS cluster deployments with production-ready configurations.

The project uses a modern Python toolchain:
- **Dependency Management:** `uv` with `pyproject.toml`
- **Code Quality:** `ruff` for linting/formatting and `mypy` for type checking.
- **Automation:** `Task` for running commands.
- **Git Hooks:** `pre-commit` for automated checks.

## Common Development Commands

All commands use Task (`Taskfile.yml`). Run from the project root directory.

### Setup & Code Quality
```bash
# Complete setup: install dependencies and pre-commit hooks
task setup

# Run all code quality checks (lint, format, typecheck)
task check

# Manually run pre-commit hooks on all files
task precommit
```

### Pulumi Stack Management
```bash
# Initialize a new stack
task pulumi:init env=staging

# Select a stack
task pulumi:select env=staging

# View stack information
task info env=staging
```

### Infrastructure Management
```bash
# Preview infrastructure changes
task preview env=staging

# Deploy infrastructure changes
task deploy env=staging

# Destroy infrastructure
task destroy env=staging

# Run code quality checks and then preview
task validate env=staging

# Configure kubectl access
task eks:kubeconfig env=staging
```

### Development and Debugging
```bash
# View detailed stack configuration
task config:list env=staging

# Set configuration values
task config:set env=staging key=node-disk-size value=200

# Refresh stack state
task refresh env=staging
```

## Architecture and Key Concepts

### Infrastructure Organization
- **Multi-environment**: Uses Pulumi stacks with environment-specific configuration via Pulumi config.
- **Dependency Management**: Uses `uv` and `pyproject.toml` for fast, reproducible dependency management.
- **Code Quality**: Enforced via `ruff`, `mypy`, and `pre-commit` hooks. Follows DRY principles with helper functions and centralized configuration.
- **Modern Libraries**: Uses `pulumi-aws` and `pulumi-awsx` for simplified AWS resource management.

### EKS Configuration Structure
- **VPC Setup**: Custom VPC with public/private subnets across 3 AZs using `awsx.ec2.Vpc`.
- **Node Groups**: Managed node groups with auto-scaling.
- **Logging**: All control plane components log to CloudWatch.
- **VPC Endpoints**: Minimal set for cost optimization.

### Key Files
- `pulumi/__main__.py`: Main entry point that calls the EKS cluster creation
- `pulumi/eks.py`: Core EKS cluster creation logic
- `pulumi/config.py`: Centralized configuration management with validation
- `pulumi/constants.py`: AWS ARNs, service endpoints, and default values
- `pulumi/iam.py`: IAM role and policy management functions
- `pulumi/vpc.py`: VPC and networking components
- `pulumi/alb.py`: ALB controller IRSA role setup
- `pulumi/types.py`: Type definitions for better type safety
- `pulumi/pyproject.toml`: Project metadata, dependencies, and tool configurations
- `pulumi/uv.lock`: Locked dependency versions for reproducible environments
- `Pulumi.yaml`: Project configuration
- `Pulumi.{staging,production}.yaml`: Stack-specific configurations
- `Taskfile.yml`: Task automation definitions with Pulumi stack management
- `.pre-commit-config.yaml`: Pre-commit hooks for automated code quality checks

### Important Implementation Details
- Cluster version: Configurable via Pulumi config
- Node AMI: AL2023_x86_64_STANDARD (Amazon Linux 2023)
- Node labeling: Worker nodes automatically labeled with environment tags
- NAT Gateways: 1 for staging (cost optimization), 3 for production (high availability)
- Security: Private endpoint enabled, public endpoint configurable
- Encryption: Optional KMS encryption for secrets
- Authentication: Standard EKS authentication using AWS CLI and kubeconfig
- VPC Endpoints: S3 (free), EC2, and STS interface endpoints for cost optimization
- Configuration: All settings managed through Pulumi config with validation
- ALB Controller: Optional IRSA role creation for AWS Load Balancer Controller

### Code Quality Features
- **Modular Architecture**: Code organized into logical modules (iam, vpc, config, etc.)
- **Type Safety**: Comprehensive type hints using Python's typing module
- **Input Validation**: Configuration validation with meaningful error messages
- **Centralized Configuration**: All settings managed through EKSConfig class
- **Security Best Practices**: KMS encryption support, configurable egress rules
- **Constants Management**: AWS ARNs and defaults in dedicated constants file
- **DRY Principles**: Reusable functions eliminate code duplication

### Before First Use
1. Ensure AWS credentials are configured
2. Run quick setup: `task setup` (installs dependencies using uv and initializes stacks)
3. Configure basic settings: `task config:set env=staging key=project-name value="MyProject"`

   Or run individual steps:
   - Install dependencies: `task pulumi:deps`
   - Initialize stacks: `task pulumi:init env=staging`
   - Set configuration: `task config:list env=staging`
   - Configure kubectl: `task eks:kubeconfig env=staging`

### Pulumi State Management
- **Remote State**: Automatically managed by Pulumi Service with encryption
- **Collaboration**: Built-in support for team collaboration and access control
- **Versioning**: Complete history of all deployments and configuration changes
- **Rollback**: Easy rollback to previous deployments
- **No Manual Setup**: No need to manage S3 buckets or DynamoDB tables
