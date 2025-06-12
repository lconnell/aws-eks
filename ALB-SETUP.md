# AWS Application Load Balancer (ALB) Setup

This document explains how to set up and use the AWS Application Load Balancer with flexible domain configuration in your EKS cluster.

## Overview

The ALB setup provides two modes:

### Mode 1: Default AWS ALB Domain (Testing)
- **Subdomain routing**: `http://api.k8s-default-xxx.us-east-1.elb.amazonaws.com` → API service, `http://argocd.k8s-default-xxx.us-east-1.elb.amazonaws.com` → ArgoCD service
- **No SSL required**: Uses HTTP for testing
- **No custom domain needed**: Perfect for development and testing

### Mode 2: Custom Domain (Production)
- **Subdomain routing**: `https://api.yourdomain.com` → API service, `https://argocd.yourdomain.com` → ArgoCD service
- **SSL/TLS termination**: Automatic SSL certificate via AWS Certificate Manager
- **Route 53 integration**: Automatic DNS record management
- **Professional URLs**: Perfect for production use

Both modes use the **AWS Load Balancer Controller** to manage ALBs via Kubernetes Ingress resources.

## Architecture

```
Internet → Route 53 → ALB → EKS Services
         ↓
    api.yourdomain.com → ALB → API Service (port 8000)
    argocd.yourdomain.com → ALB → ArgoCD Service (port 8080)
```

## Prerequisites

1. **Domain name**: You need a domain name (e.g., `yourdomain.com`)
2. **EKS cluster**: Must be deployed first
3. **Public subnets**: ALB requires public subnets (already configured in VPC)

## Configuration

Choose between the two ALB modes:

### Mode 1: Default AWS ALB Domain (Quick Testing)

Edit `terraform/staging.tfvars`:

```hcl
# Use default AWS ALB domain for testing
use_default_domain = true
enable_alb         = true
```

### Mode 2: Custom Domain (Production)

Edit `terraform/staging.tfvars`:

```hcl
# Use custom domain with SSL and Route 53
use_default_domain = false
enable_alb         = true
domain_name        = "yourdomain.com"  # Replace with your actual domain
```

### 2. Deploy Infrastructure

```bash
# Plan and apply changes
task plan env=staging
task apply env=staging
```

### 3. Access Your Services

#### For Default AWS ALB Domain (Mode 1):

Get the ALB DNS name:
```bash
task alb:status
```

Access services using subdomain routing:
- API service: `http://api.your-alb-dns-name.us-east-1.elb.amazonaws.com`
- ArgoCD service: `http://argocd.your-alb-dns-name.us-east-1.elb.amazonaws.com`

#### For Custom Domain (Mode 2):

Configure DNS nameservers:
```bash
task alb:dns:instructions
```

Update your domain's nameservers at your domain registrar to point to the Route 53 nameservers.

Access services using subdomain routing:
- API service: `https://api.yourdomain.com`
- ArgoCD service: `https://argocd.yourdomain.com`

### 4. Deploy Sample Services

```bash
# Deploy sample API and ArgoCD services
task k8s:deploy:samples

# Check status
task k8s:status
```

## Service Configuration

Services are configured in `terraform/variables.tf`:

```hcl
variable "services_config" {
  description = "Configuration for services with subdomain routing"
  type = map(object({
    subdomain = string
    port      = number
  }))
  default = {
    api = {
      subdomain = "api"
      port      = 8000
    }
    argocd = {
      subdomain = "argocd"
      port      = 8080
    }
  }
}
```

## Adding New Services

To add a new service (e.g., `dashboard`):

1. **Update variables** in `terraform/staging.tfvars`:
```hcl
services_config = {
  api = {
    subdomain = "api"
    port      = 8000
  }
  argocd = {
    subdomain = "argocd"
    port      = 8080
  }
  dashboard = {
    subdomain = "dashboard"
    port      = 3000
  }
}
```

2. **Apply changes**:
```bash
task plan env=staging
task apply env=staging
```

3. **Deploy your service** with a Kubernetes Service resource named `dashboard` on port 3000.

## SSL Certificates

### Option 1: Automatic (Recommended)
The setup automatically creates an SSL certificate via AWS Certificate Manager with:
- Primary domain: `yourdomain.com`
- SANs: `api.yourdomain.com`, `argocd.yourdomain.com`, etc.

### Option 2: Existing Certificate
If you have an existing certificate, set it in `terraform/staging.tfvars`:
```hcl
alb_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

## Monitoring and Troubleshooting

### Check ALB Status
```bash
# Show ALB and Route 53 information
task alb:status

# Check Kubernetes resources
task k8s:status

# Check ingress details
kubectl describe ingress services-ingress
```

### Common Issues

1. **Certificate validation stuck**: Check that DNS is properly configured
2. **503 errors**: Ensure your services are running and healthy
3. **DNS not resolving**: Verify nameservers are updated at domain registrar

### Logs
```bash
# Check AWS Load Balancer Controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check service logs
kubectl logs deployment/api
kubectl logs deployment/argocd
```

## Costs

The ALB setup includes:
- **Application Load Balancer**: ~$16/month + $0.008 per LCU-hour
- **Route 53 Hosted Zone**: $0.50/month + $0.40 per million queries
- **SSL Certificate**: Free via AWS Certificate Manager
- **Data transfer**: Standard AWS rates

## Security Best Practices

1. **HTTPS only**: ALB redirects HTTP to HTTPS
2. **Security groups**: ALB security group allows only 80/443
3. **Target type**: Uses IP mode for better security
4. **Health checks**: Configured on `/health` endpoint

## Cleanup

To remove ALB resources:

```bash
# Delete sample services first
task k8s:delete:samples

# Destroy infrastructure
task destroy env=staging
```

## Next Steps

1. Replace sample services with your actual applications
2. Configure monitoring and alerting
3. Set up CI/CD pipelines for automatic deployments
4. Consider using AWS WAF for additional security