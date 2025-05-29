output "cluster_endpoint" {
  description = "Endpoint for your EKS Kubernetes API server."
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids created by the EKS cluster."
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "The name of the EKS cluster."
  value       = module.eks.cluster_name
}

output "managed_node_group_arn" {
  description = "ARN of the managed node group."
  value       = module.eks.eks_managed_node_groups["main"].node_group_arn
}

output "managed_node_group_status" {
  description = "Status of the managed node group."
  value       = module.eks.eks_managed_node_groups["main"].node_group_status
}

output "managed_node_group_id" {
  description = "ID (name) of the managed node group."
  value       = module.eks.eks_managed_node_groups["main"].node_group_id
}

output "vpc_id" {
  description = "The ID of the VPC created for the EKS cluster."
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets in the VPC."
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets in the VPC."
  value       = module.vpc.public_subnets
}

output "aws_region_configured" {
  description = "The AWS region configured for the EKS cluster."
  value       = var.aws_region
}
