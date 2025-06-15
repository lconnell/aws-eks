# AWS EKS Cluster with Pulumi

This Pulumi application provisions an AWS Elastic Kubernetes Service (EKS) cluster using Python. The infrastructure follows best practices with DRY principles, helper functions for common operations, and centralized configuration management. It includes VPC, managed node groups, CloudWatch logging, and will support Application Load Balancer (ALB) integration.

## Prerequisites

1.  **Pulumi CLI:** Install Pulumi:
    - **macOS (Homebrew):** `brew install pulumi`
    - **Linux/Windows:** `curl -fsSL https://get.pulumi.com | sh`
2.  **Python 3.8+:** Required for the Pulumi Python runtime
3.  **AWS CLI:** Install and configure the AWS CLI with credentials that have permissions to create EKS clusters and related resources (VPC, IAM roles, EC2 instances, etc.).
4.  **kubectl:** Install kubectl to interact with the Kubernetes cluster.
5.  **Task CLI:** Install [Task](https://taskfile.dev/) for running automation commands.
6.  **Domain name:** Optional for ALB setup - can use default AWS domain for testing or custom domain for production.

## Directory Structure

```
aws-eks/
├── pulumi/
│   ├── __main__.py       # Main Pulumi application with EKS cluster configuration
│   ├── requirements.txt  # Python dependencies for Pulumi
│   ├── .env.example      # Environment variables template
│   ├── Pulumi.yaml       # Pulumi project configuration
│   ├── Pulumi.staging.yaml    # Stack-specific configuration for staging
│   ├── Pulumi.production.yaml # Stack-specific configuration for production
│   └── README.md         # Pulumi-specific documentation
├── Taskfile.yml          # Task definitions for common operations
├── ALB-SETUP.md          # ALB and Route 53 setup guide (to be updated for Pulumi)
├── CLAUDE.md             # Claude AI assistant guidance
└── README.md             # This file
```

## Configuration Files

*   `pulumi/__main__.py`: Main Pulumi application containing helper functions and infrastructure definition. Creates VPC (using `pulumi-awsx`), EKS cluster, managed node groups, IAM roles, and VPC endpoints. Uses best practices with DRY principles and centralized configuration.
*   `pulumi/requirements.txt`: Python dependencies including `pulumi`, `pulumi-aws`, `pulumi-awsx`, and `python-dotenv`.
*   `pulumi/.env.example`: Environment variables template for configuration - copy to `.env` and customize.
*   `pulumi/Pulumi.yaml`: Pulumi project configuration defining the project name, runtime, and description.
*   `pulumi/Pulumi.staging.yaml`: Stack-specific configuration for staging environment.
*   `pulumi/Pulumi.production.yaml`: Stack-specific configuration for production environment.
*   `pulumi/README.md`: Detailed Pulumi-specific documentation with deployment instructions.
*   `Taskfile.yml`: Contains [Task](https://taskfile.dev/) definitions for automating common operations like configuring `kubectl`, scaling node groups, and managing Pulumi stacks.
*   `ALB-SETUP.md`: Detailed guide for setting up and configuring the Application Load Balancer with Route 53 (to be updated for Pulumi).
*   `CLAUDE.md`: Guidance for Claude AI assistant when working with this repository.

## Usage

### First-Time Setup

1.  **Install Python dependencies:**
    ```bash
    task setup
    ```
    This will install all required Python packages and create a virtual environment.

2.  **Configure environment variables:**
    ```bash
    # Copy the example .env file in the pulumi directory
    cp pulumi/.env.example pulumi/.env
    
    # Edit with your specific values
    vim pulumi/.env
    ```
    
    **Required variables to update:**
    - `EKS_ADMIN_USER_ARN`: Your IAM user ARN (e.g., `arn:aws:iam::711921764356:user/devsecops`)

3.  **Initialize Pulumi stacks:**
    ```bash
    # For staging environment
    task pulumi:init env=staging
    
    # For production environment  
    task pulumi:init env=production
    ```

### Deploying Infrastructure

1.  **Review and update the `.env` file for your target environment.**
    For example, open `pulumi/.env` and review the default values. You might need to adjust `ENVIRONMENT`, `VPC_CIDR`, and region-specific settings to suit your needs.

2.  **Preview the deployment:**
    ```bash
    task preview env=staging
    # or
    task preview env=production
    ```

3.  **Deploy the infrastructure:**
    ```bash
    task deploy env=staging
    # or
    task deploy env=production
    ```

4.  **Configure kubectl:**
    Update your default kubeconfig file (usually at `~/.kube/config`).
    ```bash
    task eks:kubeconfig env=staging
    ```
    Verify cluster access.
    ```bash
    kubectl get nodes
    kubectl get svc
    ```

## ALB Setup - Two Configuration Modes

The ALB setup supports two flexible modes for different use cases:

### Mode 1: Default AWS ALB Domain (Quick Testing)

Perfect for development and testing without needing a custom domain:

```bash
# Edit terraform/staging.tfvars
use_default_domain = true
enable_alb         = true
```

**Features:**
- Subdomain routing: `http://api.k8s-default-xxx.us-east-1.elb.amazonaws.com`
- No SSL setup required
- No custom domain needed
- Perfect for development/testing

### Mode 2: Custom Domain with Route 53 (Production)

For production setups with your own domain:

```bash
# Edit terraform/staging.tfvars  
use_default_domain = false
enable_alb         = true
domain_name        = "yourdomain.com"  # Replace with your actual domain
```

**Features:**
- Subdomain routing: `https://api.yourdomain.com`
- Automatic SSL certificate via AWS Certificate Manager
- Route 53 DNS management
- Professional URLs for production

### Deployment Steps

1. **Deploy infrastructure with ALB:**
   ```bash
   task plan env=staging
   task apply env=staging
   ```

2. **For Custom Domain Mode:** Configure DNS nameservers at your domain registrar:
   ```bash
   # Get nameservers for your domain registrar
   task alb:dns:instructions
   ```

3. **Check ALB status and get URLs:**
   ```bash
   task alb:status
   ```

### Service URLs After Setup

**Default AWS Domain Mode:**
- API service: `http://api.k8s-default-xxx.us-east-1.elb.amazonaws.com`
- ArgoCD service: `http://argocd.k8s-default-xxx.us-east-1.elb.amazonaws.com`

**Custom Domain Mode:**
- API service: `https://api.yourdomain.com`
- ArgoCD service: `https://argocd.yourdomain.com`

For detailed ALB setup instructions, see [ALB-SETUP.md](ALB-SETUP.md).

## Scaling the Cluster

To scale the cluster, run:
```bash
task eks:scale env=staging desiredSize=3
# or with all parameters
task eks:scale env=staging desiredSize=3 minSize=1 maxSize=5
```

## Destroying the Cluster

To tear down the resources, run:
```bash
task destroy env=staging
# or
task destroy env=production
```

## Code Quality and Maintenance

The Pulumi code follows best practices:
```bash
# View stack outputs
task outputs env=staging

# Check stack status
task status env=staging

# View stack information
task info env=staging
```

## Task Reference

View all available tasks:
```bash
task --list
```

## Important Notes

*   **Kubernetes Version:** The `cluster_version` variable in `variables.tf` is set to a default (e.g., `1.32`). Always check the [official AWS EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) for the latest supported Kubernetes versions and update accordingly.
*   **VPC and Subnets:** This configuration creates a new VPC specifically for the EKS cluster using the `terraform-aws-modules/vpc/aws` module. This module handles the creation of public and private subnets across specified availability zones, NAT gateways (configurable, e.g., one per AZ or a single NAT gateway), and ensures all resources are tagged appropriately for EKS compatibility (e.g., `kubernetes.io/cluster/<cluster_name>=shared`).
*   **IAM Permissions:** The AWS credentials used to run Terraform need sufficient permissions to create and manage EKS clusters, IAM roles, EC2 instances, security groups, and other related resources.
*   **EKS Access Entries:** Cluster access for IAM principals is managed via EKS Access Entries, which is the successor to the `aws-auth` ConfigMap method. This configuration uses `API_AND_CONFIG_MAP` mode to support both modern access entries and node group bootstrapping.
*   **Worker Node Labeling:** Managed node groups are automatically labeled with `node-role.kubernetes.io/worker = "worker"`. This standard label helps `kubectl` display node roles correctly and can be used for scheduling workloads.
*   **ALB Configuration:** Two modes available - default AWS domain for testing (subdomain routing without SSL) or custom domain for production (subdomain routing with SSL and Route 53).
*   **State Management:**
    *   This project uses an AWS S3 remote backend with S3-native state locking (via `use_lockfile = true` in `backend.tf`)
    *   The S3 bucket is managed separately in `terraform-backend/` to avoid circular dependencies
    *   The bucket includes versioning and lifecycle policies (retains 2 newest noncurrent versions, older versions deleted after 90 days)
    *   Workspaces are used to manage multiple environments (staging/production) with isolated state files
*   **Cost:** Running an EKS cluster and associated resources will incur costs on your AWS bill. Make sure to destroy resources when they are no longer needed if you are experimenting.
