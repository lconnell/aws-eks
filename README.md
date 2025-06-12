# AWS EKS Cluster with Terraform

This Terraform configuration provisions an AWS Elastic Kubernetes Service (EKS) cluster, including the necessary VPC, with managed node groups (labeled as workers) and CloudWatch logging enabled. It uses EKS Access Entries for managing cluster access.

## Prerequisites

1.  **Terraform CLI:** Install Terraform (>= 1.3.0).
2.  **AWS CLI:** Install and configure the AWS CLI with credentials that have permissions to create EKS clusters and related resources (VPC, IAM roles, EC2 instances, etc.).
3.  **kubectl:** Install kubectl to interact with the Kubernetes cluster.

## Directory Structure

```
.aws-eks/
├── terraform/
│   ├── eks.tf            # Main EKS cluster configuration
│   ├── variables.tf      # Input variables definition
│   ├── outputs.tf        # Outputs from the Terraform configuration
│   ├── backend.tf        # S3 backend configuration
│   ├── production.tfvars # Variable values for the production environment
│   └── staging.tfvars    # Variable values for the staging environment
├── terraform-backend/
│   ├── s3-backend.tf     # S3 bucket configuration for Terraform state
│   └── README.md         # Backend setup instructions
├── Taskfile.yml          # Task definitions for common operations
└── README.md
```

## Configuration Files

*   `terraform/eks.tf`: Contains the main module calls for creating the VPC (using `terraform-aws-modules/vpc/aws`) and the EKS cluster (using `terraform-aws-modules/eks/aws`). It configures the cluster, EKS access entries (for IAM principal to Kubernetes user/group mapping), managed node groups with `node-role.kubernetes.io/worker` labels, and CloudWatch logging.
*   `terraform/variables.tf`: Defines all the input variables used by the configuration, such as AWS region, cluster version, VPC CIDR block, availability zones, and node group settings.
*   `terraform/outputs.tf`: Defines outputs like the cluster endpoint, kubeconfig, and node group ARN.
*   `terraform/backend.tf`: Configures S3 backend for remote state storage with native state locking.
*   `terraform/production.tfvars`: Example tfvars file for a production environment.
*   `terraform/staging.tfvars`: Example tfvars file for a staging environment.
*   `Taskfile.yml`: Contains [Task](https://taskfile.dev/) definitions for automating common operations like configuring `kubectl`, scaling node groups, and managing the S3 backend.
*   `terraform-backend/s3-backend.tf`: Separate Terraform configuration for creating the S3 bucket used for state storage, with versioning and lifecycle policies.

## Usage

### First-Time Setup

1.  **Create the S3 bucket for Terraform state:**
    ```bash
    task backend:create
    ```

2.  **Initialize Terraform with the S3 backend:**
    ```bash
    task backend:init
    ```

3.  **Initialize workspaces:**
    ```bash
    task terraform:workspace:init
    ```

    Or use the quick setup command to do all three steps:
    ```bash
    task setup
    ```

### Deploying Infrastructure

1.  **Review and update the `.tfvars` file for your target environment.**
    For example, open `terraform/production.tfvars` or `terraform/staging.tfvars` and review the default values. You might need to adjust `aws_region`, `vpc_cidr_block`, and `availability_zones` to suit your needs and the chosen region.

2.  **Plan the deployment:**
    ```bash
    task plan env=staging
    # or
    task plan env=production
    ```

3.  **Apply the configuration:**
    ```bash
    task apply env=staging
    # or
    task apply env=production
    ```

4.  **Configure kubectl:**
    Update your default kubeconfig file (usually at `~/.kube/config`).
    ```bash
    task eks:kubeconfig
    ```
    Set Kube context to the cluster name.
    ```bash
    task eks:kubectx
    ```
    Verify cluster access.
    ```bash
    kubectl get nodes
    kubectl get svc
    ```

## Scaling the Cluster

To scale the cluster, run:
```bash
task eks:scale desiredSize=3
# or with all parameters
task eks:scale desiredSize=3 minSize=1 maxSize=5
```

## Destroying the Cluster

To tear down the resources, run:
```bash
task destroy env=staging
# or
task destroy env=production
```

## Terraform Validation and Formatting

To maintain code quality and consistency:
```bash
# Validate Terraform configuration
task terraform:validate

# Format Terraform files
task terraform:format

# Check if files are properly formatted (useful for CI/CD)
task terraform:format:check
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
*   **EKS Access Entries:** Cluster access for IAM principals is managed via EKS Access Entries, which is the successor to the `aws-auth` ConfigMap method. This configuration sets up an access entry for the `var.eks_admin_user_arn`. If you have pre-existing access entries created outside of this Terraform setup that you wish to manage with Terraform, you will need to import them (see troubleshooting note in the Usage section).
*   **Worker Node Labeling:** Managed node groups are automatically labeled with `node-role.kubernetes.io/worker = "worker"`. This standard label helps `kubectl` display node roles correctly and can be used for scheduling workloads.
*   **State Management:**
    *   This project uses an AWS S3 remote backend with S3-native state locking (via `use_lockfile = true` in `backend.tf`)
    *   The S3 bucket is managed separately in `terraform-backend/` to avoid circular dependencies
    *   The bucket includes versioning and lifecycle policies (retains 2 newest noncurrent versions, older versions deleted after 90 days)
    *   Workspaces are used to manage multiple environments (staging/production) with isolated state files
*   **Cost:** Running an EKS cluster and associated resources will incur costs on your AWS bill. Make sure to destroy resources when they are no longer needed if you are experimenting.
