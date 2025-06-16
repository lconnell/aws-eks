"""Main entry point for Pulumi AWS EKS infrastructure."""

import os
import sys

# Add the current directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eks import create_eks_cluster

create_eks_cluster()
