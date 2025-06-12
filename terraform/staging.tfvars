aws_region         = "us-east-1"
environment        = "staging"
cluster_base_name  = "ai-agents"
eks_admin_user_arn = "arn:aws:iam::711921764356:user/devsecops"
vpc_name           = "eks-vpc"
vpc_cidr_block     = "10.20.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
num_nat_gateways   = 1

managed_node_group_instance_types = ["t3.medium"]
managed_node_group_min_size       = 2
managed_node_group_max_size       = 3
managed_node_group_desired_size   = 2

# ALB Configuration - Two modes available:

# Mode 1: Default AWS ALB domain (for testing, no custom domain required)
use_default_domain = true
enable_alb         = true

# Mode 2: Custom domain with SSL and Route 53 (for production)
# use_default_domain = false
# enable_alb         = true
# domain_name        = "your-domain.com"  # Change this to your actual domain

# Optional: Use existing SSL certificate instead of creating new one
# alb_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345..."

tags = {
  Terraform   = "true"
  Environment = "staging"
  Project     = "MyEKSProject"
}
