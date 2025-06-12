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

# ALB and Route 53 Outputs
output "domain_name" {
  description = "The domain name configured for the services (empty if using default AWS domain)"
  value       = var.domain_name
}

output "use_default_domain" {
  description = "Whether using default AWS ALB domain instead of custom domain"
  value       = var.use_default_domain
}

output "hosted_zone_id" {
  description = "Route 53 hosted zone ID (only for custom domains)"
  value       = var.enable_alb && local.use_custom_domain ? aws_route53_zone.main[0].zone_id : null
}

output "hosted_zone_name_servers" {
  description = "Name servers for the Route 53 hosted zone (only for custom domains)"
  value       = var.enable_alb && local.use_custom_domain ? aws_route53_zone.main[0].name_servers : null
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for the domain (only for custom domains)"
  value = var.enable_alb && local.use_custom_domain ? (
    var.alb_certificate_arn != "" ? var.alb_certificate_arn : (
      length(aws_acm_certificate.alb) > 0 ? aws_acm_certificate.alb[0].arn : null
    )
  ) : null
}

# Get ALB DNS name for default domain (when using default AWS domain)
data "kubernetes_ingress_v1" "default_ingress_status" {
  count = var.enable_alb && var.use_default_domain ? 1 : 0

  metadata {
    name      = kubernetes_ingress_v1.services_ingress_default[0].metadata[0].name
    namespace = kubernetes_ingress_v1.services_ingress_default[0].metadata[0].namespace
  }

  depends_on = [kubernetes_ingress_v1.services_ingress_default]
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value = var.enable_alb ? (
    var.use_default_domain && length(data.kubernetes_ingress_v1.default_ingress_status) > 0 ?
    data.kubernetes_ingress_v1.default_ingress_status[0].status[0].load_balancer[0].ingress[0].hostname :
    (local.use_custom_domain && length(data.aws_lb.ingress_alb) > 0 ? data.aws_lb.ingress_alb[0].dns_name : null)
  ) : null
}

output "service_urls" {
  description = "URLs for accessing the services"
  value = var.enable_alb ? (
    var.use_default_domain ? {
      for service_name, config in var.services_config : service_name => 
        "http://${config.subdomain}.${try(data.kubernetes_ingress_v1.default_ingress_status[0].status[0].load_balancer[0].ingress[0].hostname, "<pending>")}"
      } : (
      local.use_custom_domain ? {
        for service_name, config in var.services_config : service_name => "https://${config.subdomain}.${var.domain_name}"
      } : {}
    )
  ) : {}
}

output "usage_instructions" {
  description = "Instructions for accessing services based on domain configuration"
  value = var.enable_alb ? (
    var.use_default_domain ?
    "Using default AWS ALB domain with subdomain routing. Access services at subdomain.alb-dns-name (e.g., api.k8s-default-xxx.us-east-1.elb.amazonaws.com)." :
    "Using custom domain with subdomain routing. Configure DNS nameservers at your domain registrar and access services via subdomains."
  ) : "ALB is disabled."
}

output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM role"
  value       = var.enable_alb ? aws_iam_role.aws_load_balancer_controller[0].arn : null
}

