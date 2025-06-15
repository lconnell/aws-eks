# EKS CDK Deployment Guide

This CDK application deploys an Amazon EKS cluster with environment-specific configurations for staging and production.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js and npm installed
- Python 3.8+ installed
- AWS CDK CLI installed: `npm install -g aws-cdk`

## Setup

1. **Install Python dependencies:**
   ```bash
   cd cdk
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the example .env file
   cp .env.example .env

   # Edit .env with your specific values
   vim .env  # or use your preferred editor
   ```

   **Required variables to update in .env:**
   - `CDK_DEFAULT_ACCOUNT`: Your AWS account ID
   - `CDK_DEFAULT_REGION`: Your preferred AWS region
   - `EKS_ADMIN_ROLE_ARN` or `EKS_ADMIN_USER_ARN`: Your IAM role/user ARN for admin access

3. **Bootstrap CDK (first time only):**
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

## Configuration

All configuration is managed through the `.env` file. Key configuration options include:

### Environment Configuration
- `ENVIRONMENT`: Set to `staging` or `production`
- Environment-specific settings (instance types, node counts, NAT gateways)
- Configurable through `STAGING_*` and `PRODUCTION_*` variables

### AWS Configuration
- `CDK_DEFAULT_ACCOUNT`: AWS account ID
- `CDK_DEFAULT_REGION`: AWS region for deployment
- `EKS_ADMIN_ROLE_ARN`: IAM role ARN for cluster admin access

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

### Deploy Staging Environment (Default)
```bash
cdk deploy
```

### Deploy Production Environment
```bash
cdk deploy -c environment=production
```

### Deploy with Different Configuration
You can override .env settings using environment variables:
```bash
# Override environment
ENVIRONMENT=production cdk deploy

# Override specific settings
STAGING_DESIRED_SIZE=4 cdk deploy

# Override AWS settings
CDK_DEFAULT_REGION=us-west-2 cdk deploy
```

### Deploy with Context Variables
You can also use CDK context variables:
```bash
# Deploy production environment
cdk deploy -c environment=production
```

## Useful Commands

### Synthesize CloudFormation Template
```bash
cdk synth
```

### View Stack Differences
```bash
cdk diff
```

### List Stacks
```bash
cdk list
```

### Destroy Stack
```bash
# Staging
cdk destroy

# Production
cdk destroy -c environment=production
```

## Post-Deployment

1. **Configure kubectl:**
   After deployment, the stack outputs a kubectl configuration command:
   ```bash
   aws eks update-kubeconfig --name eks-cluster-staging --region us-east-1
   ```

2. **Verify cluster access:**
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

## Stack Features

- **Kubernetes Version:** 1.33
- **VPC Endpoints:** S3, EC2, and STS for reduced data transfer costs
- **Control Plane Logging:** All components enabled (API, Audit, Authenticator, Controller Manager, Scheduler)
- **Endpoint Access:** Both public and private access enabled
- **Node Groups:** Managed node groups in private subnets
- **Security:** IAM roles with least-privilege policies

## Environment Variables

The project uses a `.env` file for configuration. See `.env.example` for all available variables:

### Required Variables
- `CDK_DEFAULT_ACCOUNT`: AWS account ID for deployment
- `CDK_DEFAULT_REGION`: AWS region for deployment
- `EKS_ADMIN_ROLE_ARN`: IAM role ARN to grant admin access to the cluster

### Optional Variables
- `ENVIRONMENT`: Environment name (staging/production)
- `CLUSTER_VERSION`: Kubernetes version
- `ENABLE_*`: Feature toggles
- `STAGING_*` / `PRODUCTION_*`: Environment-specific configurations
- `TAG_*`: Resource tagging variables

**Note:** Environment variables take precedence over .env file values.

## Troubleshooting

1. **CDK Bootstrap Error:**
   If you see bootstrap errors, ensure you've run:
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

2. **Permission Errors:**
   Ensure your AWS credentials have permissions to create:
   - VPCs and networking resources
   - EKS clusters and node groups
   - IAM roles and policies
   - CloudWatch log groups

3. **Node Group Issues:**
   Check CloudFormation events and EKS console for detailed error messages

## Cost Optimization

The staging configuration is optimized for cost:
- Single NAT gateway (saves ~$90/month vs 3 NAT gateways)
- Smaller instance types (t3.medium)
- Minimal node count
- VPC endpoints to reduce data transfer costs

## Next Steps

After cluster deployment:
1. Install AWS Load Balancer Controller for ingress support
2. Set up cluster autoscaler for dynamic scaling
3. Configure monitoring with CloudWatch Container Insights
4. Deploy your applications using kubectl or Helm
