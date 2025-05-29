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
│   ├── production.tfvars # Variable values for the production environment
│   ├── staging.tfvars    # Variable values for the staging environment
│   └── Taskfile.yml      # Task definitions for common operations
└── README.md
```

## Configuration Files

*   `terraform/eks.tf`: Contains the main module calls for creating the VPC (using `terraform-aws-modules/vpc/aws`) and the EKS cluster (using `terraform-aws-modules/eks/aws`). It configures the cluster, EKS access entries (for IAM principal to Kubernetes user/group mapping), managed node groups with `node-role.kubernetes.io/worker` labels, and CloudWatch logging.
*   `terraform/variables.tf`: Defines all the input variables used by the configuration, such as AWS region, cluster version, VPC CIDR block, availability zones, and node group settings.
*   `terraform/outputs.tf`: Defines outputs like the cluster endpoint, kubeconfig, and node group ARN.
*   `terraform/production.tfvars`: Example tfvars file for a production environment.
*   `terraform/staging.tfvars`: Example tfvars file for a staging environment.
*   `terraform/Taskfile.yml`: Contains [Task](https://taskfile.dev/) definitions for automating common operations like configuring `kubectl` and scaling node groups.

## Usage

1.  **Navigate to the terraform directory:**
    ```bash
    cd terraform
    ```

2.  **Initialize Terraform (with S3 Remote State):**
    This configuration uses an S3 backend to store the Terraform state remotely, with S3-native locking enabled. The backend is defined in `terraform/backend.tf`.

    **Prerequisite:** Ensure the S3 bucket specified in `backend.tf` (e.g., `lee-aws-devsecops`) exists in the correct AWS region (e.g., `us-east-1`) and has **versioning enabled**.

    You will need to initialize Terraform for each workspace, providing the S3 key via `-backend-config`.

    *   **For Staging Workspace:**
        First, select or create the workspace:
        ```bash
        terraform workspace select staging
        # Or: terraform workspace new staging
        ```
        Then, initialize:
        ```bash
        terraform init -backend-config="key=eks-cluster/terraform.tfstate"
        ```

    *   **For Production Workspace:**
        First, select or create the workspace:
        ```bash
        terraform workspace select production
        # Or: terraform workspace new production
        ```
        Then, initialize:
        ```bash
        terraform init -backend-config="key=eks-cluster/terraform.tfstate"
        ```

    *   **For Default Workspace (if used):**
        ```bash
        terraform workspace select default
        terraform init -backend-config="key=eks-cluster/default/terraform.tfstate"
        ```

4.  **Review and update the `.tfvars` file for your target environment.**
    For example, open `production.tfvars` or `staging.tfvars` and review the default values. You might need to adjust `aws_region`, `vpc_cidr_block`, and `availability_zones` to suit your needs and the chosen region.

5.  **Plan the deployment:**
    For staging:
    ```bash
    task plan --env staging
    ```
    For production:
    ```bash
    task plan --env production
    ```

6.  **Apply the configuration:**
    For staging:
    ```bash
    task apply --env staging
    ```
    For production:
    ```bash
    task apply --env production
    ```

7.  **Configure kubectl:**
    Update your default kubeconfig file (usually at `~/.kube/config`).
    ```bash
    task kubeconfig
    ```
    Set Kube context to the cluster name.
    ```bash
    task kubectx
    ```
    Verify cluster access.
    ```bash
    kubectl get nodes
    kubectl get svc
    ```

## Scaling the Cluster

To scale the cluster, run:
```bash
task scale --desiredSize=0
```

## Destroying the Cluster

To tear down the resources, run:
For staging:
```bash
task destroy --env staging
```
For production:
```bash
task destroy --env production
```

## Important Notes

*   **Kubernetes Version:** The `cluster_version` variable in `variables.tf` is set to a default (e.g., `1.32`). Always check the [official AWS EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) for the latest supported Kubernetes versions and update accordingly.
*   **VPC and Subnets:** This configuration creates a new VPC specifically for the EKS cluster using the `terraform-aws-modules/vpc/aws` module. This module handles the creation of public and private subnets across specified availability zones, NAT gateways (configurable, e.g., one per AZ or a single NAT gateway), and ensures all resources are tagged appropriately for EKS compatibility (e.g., `kubernetes.io/cluster/<cluster_name>=shared`).
*   **IAM Permissions:** The AWS credentials used to run Terraform need sufficient permissions to create and manage EKS clusters, IAM roles, EC2 instances, security groups, and other related resources.
*   **EKS Access Entries:** Cluster access for IAM principals is managed via EKS Access Entries, which is the successor to the `aws-auth` ConfigMap method. This configuration sets up an access entry for the `var.eks_admin_user_arn`. If you have pre-existing access entries created outside of this Terraform setup that you wish to manage with Terraform, you will need to import them (see troubleshooting note in the Usage section).
*   **Worker Node Labeling:** Managed node groups are automatically labeled with `node-role.kubernetes.io/worker = "worker"`. This standard label helps `kubectl` display node roles correctly and can be used for scheduling workloads.
*   **State Management:**
    *   This project is configured to use an AWS S3 remote backend with S3-native state locking (via `use_lockfile = true` in `backend.tf`). This is the recommended approach for storing your state file securely and managing state locking in production and collaborative environments.
*   **Cost:** Running an EKS cluster and associated resources will incur costs on your AWS bill. Make sure to destroy resources when they are no longer needed if you are experimenting.
