# EKS Pulumi Deployment Guide

This Pulumi application deploys an Amazon EKS cluster with environment-specific configurations for staging and production, replicating the CDK implementation. The code follows best practices with DRY principles, helper functions for common operations, and centralized configuration management.

## Prerequisites

- Python 3.8+ installed
- Pulumi CLI installed:
  - **macOS (Homebrew):** `brew install pulumi`
  - **Linux/Windows:** `curl -fsSL https://get.pulumi.com | sh`
- AWS CLI configured with appropriate credentials

## Setup

1. **Install Python dependencies:**
   ```bash
   cd pulumi
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit .env with your specific values
   vim .env
   ```
   
   **Required variables to update in .env:**
   - `EKS_ADMIN_USER_ARN`: arn:aws:iam::711921764356:user/devsecops

3. **Initialize Pulumi stack:**
   ```bash
   # For staging environment
   pulumi stack init staging
   
   # For production environment  
   pulumi stack init production
   ```

## Configuration

All configuration is managed through the `.env` file.

### Environment Configuration
- `ENVIRONMENT`: Set to `staging` or `production`
- Environment-specific settings (instance types, node counts, NAT gateways)
- Configurable through `STAGING_*` and `PRODUCTION_*` variables

### AWS Configuration
- `EKS_ADMIN_USER_ARN`: IAM user ARN for cluster admin access
- AWS region is configured via Pulumi config: `pulumi config set aws:region us-east-1`

### Cluster Configuration
- `CLUSTER_VERSION`: Kubernetes version (default: 1.32)
- `NODE_DISK_SIZE`: EBS volume size for worker nodes
- `NODE_AMI_TYPE`: Node group AMI type (AL2_x86_64, AL2023_x86_64_STANDARD, BOTTLEROCKET_x86_64, etc.)
- `VPC_CIDR`: VPC CIDR block (default: 10.0.0.0/16)

### Feature Toggles
- `ENABLE_VPC_ENDPOINTS`: Enable/disable VPC endpoints for cost optimization
- `ENABLE_CLUSTER_LOGGING`: Enable/disable CloudWatch logging
- `ENABLE_PUBLIC_ENDPOINT`: Enable/disable public API endpoint
- `ENABLE_PRIVATE_ENDPOINT`: Enable/disable private API endpoint

### Default Environment Configurations

#### Staging Environment (Default)
- **Instance Type:** t3.medium
- **Node Group:** 1-3 nodes (2 desired)
- **NAT Gateways:** 1 (cost optimization)

#### Production Environment
- **Instance Type:** m5.large  
- **Node Group:** 2-10 nodes (3 desired)
- **NAT Gateways:** 3 (high availability)

## Deployment

### Deploy Staging Environment
```bash
# Select staging stack
pulumi stack select staging

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up
```

### Deploy Production Environment
```bash
# Select production stack
pulumi stack select production

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up
```

### Deploy with Different Configuration
You can override .env settings using environment variables:
```bash
# Override environment
ENVIRONMENT=production pulumi up

# Override specific settings
STAGING_DESIRED_SIZE=4 pulumi up
```

## Useful Commands

### Preview Changes
```bash
pulumi preview
```

### Deploy Infrastructure
```bash
pulumi up
```

### View Stack Outputs
```bash
pulumi stack output
```

### Get Specific Output
```bash
pulumi stack output cluster_name
pulumi stack output kubectl_command
```

### Destroy Infrastructure
```bash
pulumi destroy
```

### View Stack Information
```bash
pulumi stack
```

### Switch Between Stacks
```bash
pulumi stack select staging
pulumi stack select production
```

## Post-Deployment

1. **Configure kubectl:**
   Get the kubectl command from outputs:
   ```bash
   pulumi stack output kubectl_command
   ```
   
   Then run the returned command:
   ```bash
   aws eks update-kubeconfig --name eks-cluster-staging --region us-east-1
   ```

2. **Verify cluster access:**
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

## Stack Features

- **Kubernetes Version:** 1.32
- **VPC Endpoints:** S3, EC2, and STS for reduced data transfer costs
- **Control Plane Logging:** All components enabled (API, Audit, Authenticator, Controller Manager, Scheduler)
- **Endpoint Access:** Both public and private access enabled
- **Node Groups:** Managed node groups in private subnets
- **Security:** IAM roles with least-privilege policies
- **Authentication:** aws-auth ConfigMap for admin access

## Environment Variables

The project uses a `.env` file for configuration. See `.env.example` for all available variables:

### Required Variables
- `EKS_ADMIN_USER_ARN`: IAM user ARN to grant admin access to the cluster

### Optional Variables
- `ENVIRONMENT`: Environment name (staging/production)
- `CLUSTER_VERSION`: Kubernetes version
- `ENABLE_*`: Feature toggles
- `STAGING_*` / `PRODUCTION_*`: Environment-specific configurations
- `TAG_*`: Resource tagging variables

**Note:** Environment variables take precedence over .env file values.

## Troubleshooting

1. **Pulumi Installation Error:**
   If Pulumi CLI is not found:
   - **macOS:** `brew install pulumi`
   - **Linux/Windows:**
     ```bash
     curl -fsSL https://get.pulumi.com | sh
     export PATH=$PATH:$HOME/.pulumi/bin
     ```

2. **Permission Errors:**
   Ensure your AWS credentials have permissions to create:
   - VPCs and networking resources
   - EKS clusters and node groups
   - IAM roles and policies
   - CloudWatch log groups

3. **Node Group Issues:**
   Check Pulumi outputs and AWS console for detailed error messages:
   ```bash
   pulumi logs --follow
   ```

## Cost Optimization

The staging configuration is optimized for cost:
- Single NAT gateway (saves ~$90/month vs 3 NAT gateways)
- Smaller instance types (t3.medium)
- Minimal node count
- VPC endpoints to reduce data transfer costs

## Code Quality Features

This implementation follows software engineering best practices:

### DRY (Don't Repeat Yourself) Principles
- **Helper Functions**: Reusable functions for IAM role creation and policy attachment
- **Centralized Configuration**: All settings managed through `config_vars` dictionary
- **Environment Abstraction**: Single codebase handles multiple environments

### Easy Maintenance
- **Modular Design**: Separated concerns with dedicated functions
- **Clear Structure**: Logical grouping of related resources
- **Consistent Naming**: Standardized resource naming patterns
- **Type Hints**: Python type annotations for better code clarity

### Configuration Management
- **Environment Variables**: All settings configurable via `.env` file
- **Validation**: Input validation and sensible defaults
- **Documentation**: Comprehensive inline comments and README

## Comparison with CDK

This Pulumi implementation replicates the CDK version with these key similarities:
- Same VPC configuration with private subnets for nodes
- Identical IAM roles and policies
- Matching environment-specific configurations
- Same VPC endpoints setup
- Identical cluster logging and endpoint access

### Improvements over CDK
- **Simplified Deployment**: No need for aws-auth ConfigMap during infrastructure creation
- **Better Error Handling**: Avoids circular dependencies in Kubernetes provider
- **Cleaner Code**: Helper functions reduce code duplication

## Next Steps

After cluster deployment:
1. Install AWS Load Balancer Controller for ingress support
2. Set up cluster autoscaler for dynamic scaling
3. Configure monitoring with CloudWatch Container Insights
4. Deploy your applications using kubectl or Helm