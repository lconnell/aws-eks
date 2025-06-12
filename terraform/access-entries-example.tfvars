# Example: Additional EKS Access Entries Configuration
# Copy this to your staging.tfvars or production.tfvars and modify as needed

additional_access_entries = {
  # Example: Developer role with view access across the cluster
  developer_role = {
    principal_arn = "arn:aws:iam::123456789012:role/DeveloperRole"
    user_name     = "developer"
    type          = "STANDARD"
    policy_associations = {
      view_policy = {
        policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
        access_scope = {
          type = "cluster"
        }
      }
    }
  }

  # Example: DevOps user with edit access to specific namespaces
  devops_user = {
    principal_arn = "arn:aws:iam::123456789012:user/devops-user"
    user_name     = "devops"
    type          = "STANDARD"
    policy_associations = {
      edit_policy = {
        policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
        access_scope = {
          type       = "namespace"
          namespaces = ["default", "kube-system"]
        }
      }
    }
  }

  # Example: CI/CD service account with admin access
  cicd_service_account = {
    principal_arn = "arn:aws:iam::123456789012:role/service-role/GitHubActionsRole"
    user_name     = "github-actions"
    type          = "STANDARD"
    policy_associations = {
      admin_policy = {
        policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
        access_scope = {
          type = "cluster"
        }
      }
    }
  }

  # Example: Read-only monitoring role
  monitoring_role = {
    principal_arn = "arn:aws:iam::123456789012:role/MonitoringRole"
    user_name     = "monitoring"
    type          = "STANDARD"
    policy_associations = {
      view_policy = {
        policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
        access_scope = {
          type = "cluster"
        }
      }
    }
  }
}