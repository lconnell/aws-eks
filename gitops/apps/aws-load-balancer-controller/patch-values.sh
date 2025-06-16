#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Patching ALB Controller Application with Pulumi values...${NC}"

# Check if we're in the right directory
if [[ ! -f "application.yaml" ]]; then
    echo -e "${RED}Error: application.yaml not found. Run this script from the aws-load-balancer-controller directory.${NC}"
    exit 1
fi

# Get values from Pulumi stack outputs
echo -e "${YELLOW}Getting values from Pulumi stack...${NC}"

# Change to pulumi directory to get outputs
cd ../../../pulumi

CLUSTER_NAME=$(pulumi stack output cluster_name 2>/dev/null || echo "")
ALB_ROLE_ARN=$(pulumi stack output alb_controller_role_arn 2>/dev/null || echo "")
VPC_ID=$(pulumi stack output vpc_id 2>/dev/null || echo "")

# Go back to the app directory
cd ../gitops/apps/aws-load-balancer-controller

# Validate required values
if [[ -z "$CLUSTER_NAME" ]]; then
    echo -e "${RED}Error: Could not get cluster_name from Pulumi stack${NC}"
    exit 1
fi

if [[ -z "$ALB_ROLE_ARN" ]]; then
    echo -e "${RED}Error: Could not get alb_controller_role_arn from Pulumi stack${NC}"
    echo -e "${YELLOW}Make sure enable-alb-controller is set to true in Pulumi config${NC}"
    exit 1
fi

if [[ -z "$VPC_ID" ]]; then
    echo -e "${RED}Error: Could not get vpc_id from Pulumi stack${NC}"
    exit 1
fi

echo -e "${GREEN}Found Pulumi values:${NC}"
echo -e "  Cluster Name: ${YELLOW}$CLUSTER_NAME${NC}"
echo -e "  ALB Role ARN: ${YELLOW}$ALB_ROLE_ARN${NC}"
echo -e "  VPC ID: ${YELLOW}$VPC_ID${NC}"

# Create patched version
echo -e "${YELLOW}Creating patched application.yaml...${NC}"
cp application.yaml application-patched.yaml

# Replace placeholders
sed -i.bak "s|CLUSTER_NAME_PLACEHOLDER|$CLUSTER_NAME|g" application-patched.yaml
sed -i.bak "s|ALB_ROLE_ARN_PLACEHOLDER|$ALB_ROLE_ARN|g" application-patched.yaml
sed -i.bak "s|VPC_ID_PLACEHOLDER|$VPC_ID|g" application-patched.yaml

# Clean up backup file
rm application-patched.yaml.bak

echo -e "${GREEN}Successfully created application-patched.yaml${NC}"
echo -e "${YELLOW}To deploy the ALB Controller:${NC}"
echo -e "1. Apply the ArgoCD Application: ${GREEN}kubectl apply -f application-patched.yaml${NC}"
echo -e "2. Check the application status: ${GREEN}kubectl get application aws-load-balancer-controller -n argocd${NC}"
echo -e "3. Watch the deployment: ${GREEN}kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller${NC}"
