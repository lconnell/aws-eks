#------------------------------------------------------------------------------
# Locals for domain logic
#------------------------------------------------------------------------------
locals {
  # Use custom domain only if provided and not using default domain
  use_custom_domain = var.enable_alb && !var.use_default_domain && var.domain_name != ""
  # Determine if we should create Route 53 resources
  create_route53 = local.use_custom_domain
  # Determine if we should create SSL certificate
  create_ssl_cert = local.use_custom_domain && var.alb_certificate_arn == ""
}

#------------------------------------------------------------------------------
# Route 53 Hosted Zone (only for custom domains)
#------------------------------------------------------------------------------
resource "aws_route53_zone" "main" {
  count = local.create_route53 ? 1 : 0

  name = var.domain_name

  tags = merge(
    var.tags,
    {
      Name        = var.domain_name
      Environment = var.environment
      Purpose     = "EKS ALB DNS"
    }
  )
}

#------------------------------------------------------------------------------
# ACM Certificate for ALB (only for custom domains)
#------------------------------------------------------------------------------
resource "aws_acm_certificate" "alb" {
  count = local.create_ssl_cert ? 1 : 0

  domain_name = var.domain_name
  subject_alternative_names = [
    for service_name, config in var.services_config : "${config.subdomain}.${var.domain_name}"
  ]

  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.domain_name}-alb-cert"
      Environment = var.environment
    }
  )
}

# Certificate validation records (only for custom domains)
resource "aws_route53_record" "cert_validation" {
  for_each = local.create_ssl_cert ? {
    for dvo in aws_acm_certificate.alb[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id
}

# Certificate validation (only for custom domains)
resource "aws_acm_certificate_validation" "alb" {
  count = local.create_ssl_cert ? 1 : 0

  certificate_arn         = aws_acm_certificate.alb[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
}

#------------------------------------------------------------------------------
# AWS Load Balancer Controller IAM Role
#------------------------------------------------------------------------------
data "aws_iam_policy_document" "aws_load_balancer_controller_assume_role_policy" {
  count = var.enable_alb ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = [module.eks.oidc_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "aws_load_balancer_controller" {
  count = var.enable_alb ? 1 : 0

  name               = "${local.cluster_name}-aws-load-balancer-controller"
  assume_role_policy = data.aws_iam_policy_document.aws_load_balancer_controller_assume_role_policy[0].json

  tags = merge(
    var.tags,
    {
      Name        = "${local.cluster_name}-aws-load-balancer-controller"
      Environment = var.environment
    }
  )
}

# Attach the AWS Load Balancer Controller policy
resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller" {
  count = var.enable_alb ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
  role       = aws_iam_role.aws_load_balancer_controller[0].name
}

# Additional IAM policy for ALB controller
resource "aws_iam_policy" "aws_load_balancer_controller_additional" {
  count = var.enable_alb ? 1 : 0

  name = "${local.cluster_name}-aws-load-balancer-controller-additional"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:CreateServiceLinkedRole",
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeTags",
          "ec2:GetCoipPoolUsage",
          "ec2:DescribeCoipPools",
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeLoadBalancerAttributes",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:DescribeListenerCertificates",
          "elasticloadbalancing:DescribeSSLPolicies",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetGroupAttributes",
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "iam:ListServerCertificates",
          "iam:GetServerCertificate",
          "waf-regional:GetWebACL",
          "waf-regional:GetWebACLForResource",
          "waf-regional:AssociateWebACL",
          "waf-regional:DisassociateWebACL",
          "wafv2:GetWebACL",
          "wafv2:GetWebACLForResource",
          "wafv2:AssociateWebACL",
          "wafv2:DisassociateWebACL",
          "shield:DescribeProtection",
          "shield:GetSubscriptionState",
          "shield:DescribeSubscription",
          "shield:CreateProtection",
          "shield:DeleteProtection"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSecurityGroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*:*:security-group/*"
        Condition = {
          StringEquals = {
            "ec2:CreateAction" = "CreateSecurityGroup"
          }
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:DeleteListener",
          "elasticloadbalancing:CreateRule",
          "elasticloadbalancing:DeleteRule"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:RemoveTags"
        ]
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
        ]
        Condition = {
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster"  = "true"
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:ModifyLoadBalancerAttributes",
          "elasticloadbalancing:SetIpAddressType",
          "elasticloadbalancing:SetSecurityGroups",
          "elasticloadbalancing:SetSubnets",
          "elasticloadbalancing:DeleteLoadBalancer",
          "elasticloadbalancing:ModifyTargetGroup",
          "elasticloadbalancing:ModifyTargetGroupAttributes",
          "elasticloadbalancing:DeleteTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets"
        ]
        Resource = "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${local.cluster_name}-aws-load-balancer-controller-additional"
      Environment = var.environment
    }
  )
}

resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller_additional" {
  count = var.enable_alb ? 1 : 0

  policy_arn = aws_iam_policy.aws_load_balancer_controller_additional[0].arn
  role       = aws_iam_role.aws_load_balancer_controller[0].name
}

#------------------------------------------------------------------------------
# Kubernetes Providers Configuration
#------------------------------------------------------------------------------
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

#------------------------------------------------------------------------------
# AWS Load Balancer Controller Deployment
#------------------------------------------------------------------------------
resource "helm_release" "aws_load_balancer_controller" {
  count = var.enable_alb ? 1 : 0

  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.7.2"

  set {
    name  = "clusterName"
    value = module.eks.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.aws_load_balancer_controller[0].arn
  }

  set {
    name  = "region"
    value = var.aws_region
  }

  set {
    name  = "vpcId"
    value = module.vpc.vpc_id
  }

  depends_on = [
    module.eks,
    aws_iam_role_policy_attachment.aws_load_balancer_controller,
    aws_iam_role_policy_attachment.aws_load_balancer_controller_additional
  ]
}

#------------------------------------------------------------------------------
# Kubernetes Ingress Resource for Custom Domain Routing
#------------------------------------------------------------------------------
resource "kubernetes_ingress_v1" "services_ingress_custom" {
  count = var.enable_alb && local.use_custom_domain ? 1 : 0

  metadata {
    name      = "services-ingress"
    namespace = "default"
    annotations = {
      "kubernetes.io/ingress.class"                            = "alb"
      "alb.ingress.kubernetes.io/scheme"                       = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"                  = "ip"
      "alb.ingress.kubernetes.io/certificate-arn"              = var.alb_certificate_arn != "" ? var.alb_certificate_arn : aws_acm_certificate_validation.alb[0].certificate_arn
      "alb.ingress.kubernetes.io/listen-ports"                 = "[{\"HTTP\": 80}, {\"HTTPS\": 443}]"
      "alb.ingress.kubernetes.io/ssl-redirect"                 = "443"
      "alb.ingress.kubernetes.io/healthcheck-path"             = "/health"
      "alb.ingress.kubernetes.io/healthcheck-interval-seconds" = "15"
      "alb.ingress.kubernetes.io/healthcheck-timeout-seconds"  = "5"
      "alb.ingress.kubernetes.io/success-codes"                = "200"
      "alb.ingress.kubernetes.io/healthy-threshold-count"      = "2"
      "alb.ingress.kubernetes.io/unhealthy-threshold-count"    = "2"
    }
  }

  spec {
    dynamic "rule" {
      for_each = var.services_config
      content {
        host = "${rule.value.subdomain}.${var.domain_name}"
        http {
          path {
            path      = "/"
            path_type = "Prefix"
            backend {
              service {
                name = rule.key
                port {
                  number = rule.value.port
                }
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    helm_release.aws_load_balancer_controller,
    aws_acm_certificate_validation.alb
  ]
}

#------------------------------------------------------------------------------
# Kubernetes Ingress Resource for Default AWS Domain (Subdomain routing)
#------------------------------------------------------------------------------
resource "kubernetes_ingress_v1" "services_ingress_default" {
  count = var.enable_alb && var.use_default_domain ? 1 : 0

  metadata {
    name      = "services-ingress-default"
    namespace = "default"
    annotations = {
      "kubernetes.io/ingress.class"                            = "alb"
      "alb.ingress.kubernetes.io/scheme"                       = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"                  = "ip"
      "alb.ingress.kubernetes.io/listen-ports"                 = "[{\"HTTP\": 80}]"
      "alb.ingress.kubernetes.io/healthcheck-path"             = "/health"
      "alb.ingress.kubernetes.io/healthcheck-interval-seconds" = "15"
      "alb.ingress.kubernetes.io/healthcheck-timeout-seconds"  = "5"
      "alb.ingress.kubernetes.io/success-codes"                = "200"
      "alb.ingress.kubernetes.io/healthy-threshold-count"      = "2"
      "alb.ingress.kubernetes.io/unhealthy-threshold-count"    = "2"
    }
  }

  spec {
    dynamic "rule" {
      for_each = var.services_config
      content {
        # Use subdomain routing with wildcard host (ALB will accept api.*, argocd.* etc.)
        host = "${rule.value.subdomain}.*"
        http {
          path {
            path      = "/"
            path_type = "Prefix"
            backend {
              service {
                name = rule.key
                port {
                  number = rule.value.port
                }
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    helm_release.aws_load_balancer_controller
  ]
}

#------------------------------------------------------------------------------
# Route 53 Records for Services (Custom Domain Only)
#------------------------------------------------------------------------------
# Get ALB information for custom domain
data "kubernetes_ingress_v1" "services_ingress_status" {
  count = var.enable_alb && local.use_custom_domain ? 1 : 0

  metadata {
    name      = kubernetes_ingress_v1.services_ingress_custom[0].metadata[0].name
    namespace = kubernetes_ingress_v1.services_ingress_custom[0].metadata[0].namespace
  }

  depends_on = [kubernetes_ingress_v1.services_ingress_custom]
}

# Get ALB DNS name from AWS for custom domain
data "aws_lb" "ingress_alb" {
  count = var.enable_alb && local.use_custom_domain && length(data.kubernetes_ingress_v1.services_ingress_status) > 0 ? 1 : 0

  # Extract ALB name from hostname (format: k8s-default-servicesXXX-XXXXXXXXXX.us-east-1.elb.amazonaws.com)
  name = split(".", data.kubernetes_ingress_v1.services_ingress_status[0].status[0].load_balancer[0].ingress[0].hostname)[0]

  depends_on = [data.kubernetes_ingress_v1.services_ingress_status]
}

# Create Route 53 records for each service subdomain (custom domain only)
resource "aws_route53_record" "services" {
  for_each = var.enable_alb && local.use_custom_domain && length(data.aws_lb.ingress_alb) > 0 ? var.services_config : {}

  zone_id = aws_route53_zone.main[0].zone_id
  name    = "${each.value.subdomain}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = data.aws_lb.ingress_alb[0].dns_name
    zone_id                = data.aws_lb.ingress_alb[0].zone_id
    evaluate_target_health = true
  }

  depends_on = [
    data.aws_lb.ingress_alb,
    kubernetes_ingress_v1.services_ingress_custom
  ]
}