# Example: Using aws_eks_access_entry resources directly (standalone approach)
# This file is for reference only - the main configuration uses the 
# terraform-aws-modules/eks/aws module's access_entries parameter

# Note: Uncomment and modify these resources if you want to manage access entries
# directly instead of using the EKS module's access_entries parameter

/*
# Direct access entry resource for admin user
resource "aws_eks_access_entry" "admin_user" {
  cluster_name  = module.eks.cluster_name
  principal_arn = var.eks_admin_user_arn
  user_name     = local.admin_principal_name
  type          = "STANDARD"

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-admin-access-entry"
  })
}

# Policy association for the admin user access entry
resource "aws_eks_access_policy_association" "admin_user_policy" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_eks_access_entry.admin_user.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}

# Example: Developer role with namespace-scoped access
resource "aws_eks_access_entry" "developer_role" {
  cluster_name  = module.eks.cluster_name
  principal_arn = "arn:aws:iam::123456789012:role/DeveloperRole"
  user_name     = "developer"
  type          = "STANDARD"

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-developer-access-entry"
  })
}

resource "aws_eks_access_policy_association" "developer_view_policy" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_eks_access_entry.developer_role.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"

  access_scope {
    type       = "namespace"
    namespaces = ["default", "development"]
  }
}

# Example: Service account with edit access to specific namespaces
resource "aws_eks_access_entry" "service_account" {
  cluster_name  = module.eks.cluster_name
  principal_arn = "arn:aws:iam::123456789012:role/service-role/AppServiceRole"
  user_name     = "app-service"
  type          = "STANDARD"

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-service-access-entry"
  })
}

resource "aws_eks_access_policy_association" "service_edit_policy" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_eks_access_entry.service_account.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"

  access_scope {
    type       = "namespace"
    namespaces = ["application", "staging"]
  }
}
*/