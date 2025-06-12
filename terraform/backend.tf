terraform {
  backend "s3" {
    # Bucket must be created first using terraform-backend/s3-backend.tf
    bucket       = "711921764356-eks-terraform-state" # Replace with your actual bucket name
    key          = "eks-cluster/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true # Enables S3-native state locking
  }
}
