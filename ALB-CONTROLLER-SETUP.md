# AWS Load Balancer Controller Setup Guide

This guide provides instructions for installing the AWS Load Balancer Controller in your EKS cluster using GitOps.

## Prerequisites

Before installing the ALB Controller, ensure you have:

1. **EKS cluster deployed with Pulumi** with `enable-alb-controller` set to `true`
2. **kubectl configured** to access your cluster
3. **Helm 3** installed on your local machine
4. **Exported Pulumi outputs** available

## Step 1: Get Required Values from Pulumi

First, export the necessary values from your Pulumi stack:

```bash
# Export all stack outputs
pulumi stack output -j > stack-outputs.json

# Get specific values
export CLUSTER_NAME=$(pulumi stack output cluster_name)
export ALB_ROLE_ARN=$(pulumi stack output alb_controller_role_arn)
export AWS_REGION=us-east-1  # Or your configured region
```

## Step 2: Install AWS Load Balancer Controller

### Add the EKS Helm repository

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update
```

### Install the controller using Helm

Create a `values.yaml` file for the ALB Controller:

```yaml
# alb-controller-values.yaml
clusterName: ${CLUSTER_NAME}
serviceAccount:
  create: true
  name: aws-load-balancer-controller
  annotations:
    eks.amazonaws.com/role-arn: ${ALB_ROLE_ARN}
region: ${AWS_REGION}
vpcId: ${VPC_ID}
enableServiceMutatorWebhook: true
ingressClass: alb
```

Install the controller:

```bash
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  -f alb-controller-values.yaml \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ALB_ROLE_ARN \
  --set region=$AWS_REGION \
  --version 1.11.0
```

## Step 3: Verify Installation

Check that the controller is running:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## Step 4: Example Ingress Configuration

Here's a simple example using the default AWS ALB domain:

```yaml
# example-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
spec:
  ingressClassName: alb
  rules:
    - host: api.elb.amazonaws.com  # This will be replaced with actual ALB DNS
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8000
    - host: app.elb.amazonaws.com  # This will be replaced with actual ALB DNS
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-service
                port:
                  number: 3000
```

## Step 5: Deploy a Test Application

Create a simple test application:

```yaml
# test-app.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: test-app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-server
  namespace: test-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo-server
  template:
    metadata:
      labels:
        app: echo-server
    spec:
      containers:
      - name: echo-server
        image: ealen/echo-server:latest
        ports:
        - containerPort: 80
        env:
        - name: PORT
          value: "80"
---
apiVersion: v1
kind: Service
metadata:
  name: echo-service
  namespace: test-app
spec:
  type: ClusterIP
  selector:
    app: echo-server
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echo-ingress
  namespace: test-app
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: echo-service
                port:
                  number: 80
```

Deploy the test application:

```bash
kubectl apply -f test-app.yaml
```

## Step 6: Get ALB URL

After creating an Ingress, get the ALB URL:

```bash
kubectl get ingress -n test-app echo-ingress
```

The ALB DNS name will appear in the `ADDRESS` column. It may take 2-3 minutes for the ALB to be provisioned.

## GitOps Integration

For GitOps deployment, structure your repository as follows:

```
gitops-repo/
├── base/
│   ├── aws-load-balancer-controller/
│   │   ├── namespace.yaml
│   │   ├── service-account.yaml
│   │   └── helm-release.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── production/
│       ├── kustomization.yaml
│       └── patches/
└── applications/
    └── example-app/
        ├── deployment.yaml
        ├── service.yaml
        └── ingress.yaml
```

### Example Flux HelmRelease for ALB Controller:

```yaml
# base/aws-load-balancer-controller/helm-release.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
spec:
  interval: 5m
  chart:
    spec:
      chart: aws-load-balancer-controller
      version: "1.11.0"
      sourceRef:
        kind: HelmRepository
        name: eks-charts
        namespace: flux-system
  values:
    clusterName: ${cluster_name}
    serviceAccount:
      create: true
      name: aws-load-balancer-controller
      annotations:
        eks.amazonaws.com/role-arn: ${alb_controller_role_arn}
    region: ${aws_region}
    ingressClass: alb
```

## Advanced Ingress Annotations

Common annotations for production use:

```yaml
annotations:
  # ALB Configuration
  alb.ingress.kubernetes.io/scheme: internet-facing
  alb.ingress.kubernetes.io/target-type: ip
  alb.ingress.kubernetes.io/load-balancer-name: my-app-alb

  # Health Check
  alb.ingress.kubernetes.io/healthcheck-path: /health
  alb.ingress.kubernetes.io/healthcheck-interval-seconds: "30"
  alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
  alb.ingress.kubernetes.io/healthy-threshold-count: "2"
  alb.ingress.kubernetes.io/unhealthy-threshold-count: "3"

  # SSL/TLS (when using custom domain)
  alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/cert-id
  alb.ingress.kubernetes.io/ssl-redirect: "443"
  alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'

  # Tags
  alb.ingress.kubernetes.io/tags: Environment=staging,Team=platform
```

## Troubleshooting

### Check controller logs:
```bash
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

### Common issues:
1. **ALB not created**: Check IRSA role permissions
2. **Targets unhealthy**: Verify security groups and health check path
3. **503 errors**: Ensure services and pods are running

### Useful commands:
```bash
# Describe ingress
kubectl describe ingress -n <namespace> <ingress-name>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# View controller configuration
kubectl get configmap -n kube-system aws-load-balancer-controller-leader -o yaml
```

## Cleanup

To remove the ALB Controller:

```bash
# Delete all Ingress resources first (important!)
kubectl delete ingress --all --all-namespaces

# Uninstall the controller
helm uninstall aws-load-balancer-controller -n kube-system
```

## Next Steps

1. Create Ingress resources for your applications
2. Configure monitoring and alerts for ALBs
3. Set up custom domains with Route 53 (optional)
4. Implement WAF rules for security (optional)
