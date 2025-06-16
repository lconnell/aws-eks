"""Constants for AWS EKS infrastructure."""

# AWS Managed Policy ARNs
AWS_EKS_CLUSTER_POLICY = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
AWS_EKS_WORKER_NODE_POLICY = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
AWS_EKS_CNI_POLICY = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
AWS_EC2_CONTAINER_REGISTRY_READONLY = (
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
)
AWS_ELB_FULL_ACCESS = "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"

# OIDC Configuration
OIDC_THUMBPRINT = "9e99a48a9960b14926bb7f3b02e22da2b0ab7280"
OIDC_CLIENT_ID = "sts.amazonaws.com"

# Network Configuration
DEFAULT_EGRESS_CIDR = "0.0.0.0/0"
HTTPS_PORT = 443

# Service Endpoints
AWS_SERVICE_ENDPOINTS = ["s3", "ec2", "sts"]

# Default Values
DEFAULT_NODE_DISK_SIZE = 100
DEFAULT_NODE_AMI_TYPE = "AL2023_x86_64_STANDARD"
DEFAULT_VPC_CIDR = "10.0.0.0/16"
DEFAULT_VPC_MAX_AZS = 3

# Cluster Logging Types
CLUSTER_LOG_TYPES = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

# ALB Controller
ALB_CONTROLLER_NAMESPACE = "kube-system"
ALB_CONTROLLER_SERVICE_ACCOUNT = "aws-load-balancer-controller"
ALB_CONTROLLER_CHART_VERSION = "1.6.1"
