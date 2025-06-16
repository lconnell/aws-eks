# GitOps Configuration

This directory contains the GitOps configuration for managing applications on your EKS cluster using ArgoCD.

## Directory Structure

```
gitops/
├── bootstrap/                 # ArgoCD installation and initial setup
│   ├── base/                 # Base ArgoCD configuration
│   └── overlays/             # Environment-specific configurations
│       ├── staging/
│       └── production/
├── apps/                     # Application definitions
│   ├── argocd/              # ArgoCD self-management
│   ├── aws-load-balancer-controller/  # ALB Controller
│   └── demo-apps/           # Example applications
└── projects/                # ArgoCD projects (for advanced use)
```

## Quick Start

### 1. Prerequisites

- EKS cluster deployed with Pulumi (`enable-alb-controller: true`)
- kubectl configured to access your cluster
- Helm 3 installed

### 2. Bootstrap ArgoCD

```bash
# Navigate to bootstrap directory
cd gitops/bootstrap/base

# Install ArgoCD
./install-argocd.sh

# Access ArgoCD UI (in a new terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser to https://localhost:8080
# Login: admin / (password from install script output)
```

### 3. Deploy ALB Controller

```bash
# Navigate to ALB Controller directory
cd ../../apps/aws-load-balancer-controller

# Patch with Pulumi values
./patch-values.sh

# Deploy via ArgoCD
kubectl apply -f application-patched.yaml

# Monitor deployment
kubectl get application aws-load-balancer-controller -n argocd
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### 4. Deploy Demo Applications (Optional)

```bash
# Navigate to demo apps directory
cd ../demo-apps

# Update the repository URL in application.yaml
# Then apply
kubectl apply -f application.yaml

# Check ingress
kubectl get ingress -n demo-apps
```

## Application Management

### Adding New Applications

1. Create a new directory under `apps/`
2. Add your Kubernetes manifests or create an ArgoCD Application
3. Apply the Application resource to ArgoCD

### Environment-Specific Configurations

Use Kustomize overlays in the `bootstrap/overlays/` directory for environment-specific configurations.

## Security Considerations

- ArgoCD is configured with basic settings for development/testing
- For production, consider:
  - Enabling RBAC and SSO
  - Setting up proper ingress with SSL certificates
  - Configuring resource limits and quotas
  - Implementing proper secret management

## Troubleshooting

### ArgoCD Issues

```bash
# Check ArgoCD status
kubectl get pods -n argocd

# Check ArgoCD logs
kubectl logs -n argocd deployment/argocd-server
kubectl logs -n argocd deployment/argocd-application-controller

# Restart ArgoCD
kubectl rollout restart deployment/argocd-server -n argocd
```

### ALB Controller Issues

```bash
# Check ALB Controller status
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check ALB Controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check ArgoCD Application status
kubectl describe application aws-load-balancer-controller -n argocd
```

### Common Issues

1. **Application stuck in "OutOfSync"**: Check the repository URL and path in the Application spec
2. **ALB not created**: Verify IRSA role permissions and subnet tags
3. **ArgoCD UI not accessible**: Check service and ingress configuration

## Next Steps

1. Set up your own Git repository for GitOps
2. Update repository URLs in Application manifests
3. Configure CI/CD pipelines to update image tags
4. Set up monitoring and alerting for ArgoCD and applications
