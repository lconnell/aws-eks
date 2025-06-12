aws_region         = "us-east-1"
environment        = "production"
cluster_base_name  = "ai-agents"
eks_admin_user_arn = "arn:aws:iam::711921764356:user/devsecops"
vpc_name           = "eks-vpc"
vpc_cidr_block     = "10.10.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
num_nat_gateways   = 3 # One per AZ for production

managed_node_group_instance_types = ["m5.large"]
managed_node_group_min_size       = 2
managed_node_group_max_size       = 5
managed_node_group_desired_size   = 2

tags = {
  Terraform   = "true"
  Environment = "production"
  Project     = "MyEKSProject"
}
