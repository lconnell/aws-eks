#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing ArgoCD via Helm...${NC}"

# Add ArgoCD Helm repository
echo -e "${YELLOW}Adding ArgoCD Helm repository...${NC}"
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create namespace
echo -e "${YELLOW}Creating ArgoCD namespace...${NC}"
kubectl apply -f argocd-namespace.yaml

# Apply ConfigMap with values
echo -e "${YELLOW}Applying ArgoCD configuration...${NC}"
kubectl apply -f argocd-helm-chart.yaml

# Install ArgoCD
echo -e "${YELLOW}Installing ArgoCD with Helm...${NC}"
helm install argocd argo/argo-cd \
  --namespace argocd \
  --values <(kubectl get configmap argocd-helm-values -n argocd -o jsonpath='{.data.values\.yaml}') \
  --version 7.7.8

# Wait for ArgoCD to be ready
echo -e "${YELLOW}Waiting for ArgoCD to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
echo -e "${GREEN}ArgoCD installation complete!${NC}"
echo -e "${YELLOW}Getting initial admin password...${NC}"
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo -e "${GREEN}ArgoCD admin password: ${ARGOCD_PASSWORD}${NC}"

echo -e "${YELLOW}To access ArgoCD:${NC}"
echo -e "1. Port forward: ${GREEN}kubectl port-forward svc/argocd-server -n argocd 8080:443${NC}"
echo -e "2. Open browser: ${GREEN}https://localhost:8080${NC}"
echo -e "3. Login with username: ${GREEN}admin${NC} and password above"
