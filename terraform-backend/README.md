# Terraform Backend S3 Bucket Setup

This directory contains the Terraform configuration to create the S3 bucket used for storing Terraform state files for the EKS cluster.

## Setup Instructions

1. **Create the S3 bucket:**
   ```bash
   cd terraform-backend
   terraform init
   terraform apply
   ```

2. **Note the bucket name from the output:**
   ```bash
   terraform output bucket_name
   ```

3. **Update the main Terraform backend configuration:**
   - Edit `../terraform/backend.tf`
   - Replace `PLACEHOLDER-eks-terraform-state` with your actual bucket name

4. **Initialize the main Terraform configuration:**
   ```bash
   cd ../terraform
   terraform init
   terraform workspace new staging
   terraform workspace new production
   ```

## S3 Bucket Features

- **Versioning**: Enabled to track state file history
- **Lifecycle Policy**: Retains 2 newest noncurrent versions, older versions deleted after 90 days
- **Encryption**: Server-side encryption with AES256
- **Access**: Public access blocked
- **Naming**: Default format is `{account-id}-eks-terraform-state`

## Workspace Usage

The main Terraform configuration uses workspaces to manage multiple environments:
- State files are stored as: `eks-cluster/terraform.tfstate` (workspace-aware)
- Each workspace (staging/production) maintains its own state file