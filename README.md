# AWS EKS Cluster with Terraform

This Terraform configuration provisions an AWS Elastic Kubernetes Service (EKS) cluster with managed node groups and CloudWatch logging enabled.

## Prerequisites

1.  **Terraform CLI:** Install Terraform (>= 1.3.0).
2.  **AWS CLI:** Install and configure the AWS CLI with credentials that have permissions to create EKS clusters and related resources (VPC, IAM roles, EC2 instances, etc.).
3.  **kubectl:** Install kubectl to interact with the Kubernetes cluster.
4.  **kubectl:** Install kubectl to interact with the Kubernetes cluster.

## Directory Structure

```
.aws-eks/
├── terraform/
│   ├── eks.tf            # Main EKS cluster configuration
│   ├── variables.tf      # Input variables definition
│   ├── outputs.tf        # Outputs from the Terraform configuration
│   ├── production.tfvars # Variable values for the production environment
│   └── staging.tfvars    # Variable values for the staging environment
└── README.md
```

## Configuration Files

*   `terraform/eks.tf`: Contains the main module call to the `terraform-aws-modules/eks/aws` module, configuring the cluster, managed node groups, and CloudWatch logging.
*   `terraform/variables.tf`: Defines all the input variables used by the configuration, such as AWS region, cluster version, VPC CIDR block, availability zones, and node group settings.
*   `terraform/outputs.tf`: Defines outputs like the cluster endpoint, kubeconfig, and node group ARN.
*   `terraform/production.tfvars`: Example tfvars file for a production environment. **You may need to update `availability_zones` based on your AWS region (`us-east-1` by default for prod).**
*   `terraform/staging.tfvars`: Example tfvars file for a staging environment. **You may need to update `availability_zones` based on your AWS region (`us-west-2` by default for staging).**

## Usage

1.  **Navigate to the terraform directory:**
    ```bash
    cd terraform
    ```

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Create a workspace (optional but recommended for multiple environments):**
    For staging:
    ```bash
    terraform workspace new staging
    # terraform workspace select staging # If it already exists
    ```
    For production:
    ```bash
    terraform workspace new production
    # terraform workspace select production # If it already exists
    ```

4.  **Review and update the `.tfvars` file for your target environment.**
    For example, open `production.tfvars` or `staging.tfvars` and review the default values. You might need to adjust `aws_region`, `vpc_cidr_block`, and `availability_zones` to suit your needs and the chosen region.

5.  **Plan the deployment:**
    For staging:
    ```bash
    terraform plan -var-file="staging.tfvars" -out stg-plan.out
    ```
    For production:
    ```bash
    terraform plan -var-file="production.tfvars" -out prd-plan.out
    ```

6.  **Apply the configuration:**
    For staging:
    ```bash
    terraform apply stg-plan.out
    ```
    For production:
    ```bash
    terraform apply prd-plan.out
    ```
    Confirm the action by typing `yes` when prompted.

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
terraform destroy -var-file="staging.tfvars"
```
For production:
```bash
terraform destroy -var-file="production.tfvars"
```
Confirm the action by typing `yes` when prompted.

## Important Notes

*   **Kubernetes Version:** The `cluster_version` variable in `variables.tf` is set to a default (e.g., `1.32`). Always check the [official AWS EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) for the latest supported Kubernetes versions and update accordingly.
*   **VPC and Subnets:** This configuration now creates a new VPC and subnets. The VPC module (`terraform-aws-modules/vpc/aws`) handles the creation of public and private subnets, NAT gateways (configurable), and appropriate tagging for EKS compatibility.
*   **IAM Permissions:** The AWS credentials used to run Terraform need sufficient permissions to create and manage EKS clusters, IAM roles, EC2 instances, security groups, and other related resources.
*   **Cost:** Running an EKS cluster and associated resources will incur costs on your AWS bill. Make sure to destroy resources when they are no longer needed if you are experimenting.
