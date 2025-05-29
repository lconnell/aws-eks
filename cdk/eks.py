from aws_cdk import (
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    App, Stack, CfnOutput
)
from aws_cdk_lambda_layer_kubectl import KubectlLayer  # Correct import

class EksClusterStack(Stack):
    def __init__(self, scope: App, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC (or use an existing one)
        vpc = ec2.Vpc(self, "EksVpc", max_azs=2)  # 2 Availability Zones

        # Define the kubectl layer
        kubectl = KubectlLayer(self, "KubectlLayer")

        # Define the EKS cluster
        cluster = eks.Cluster(
            self,
            "MyEksCluster",
            vpc=vpc,
            default_capacity=0,  # No default capacity; we'll add a node group manually
            version=eks.KubernetesVersion.V1_28,  # Specify Kubernetes version
            kubectl_layer=kubectl  # Pass the kubectl layer
        )

        # Add a managed node group
        cluster.add_nodegroup_capacity(
            "Nodegroup",
            instance_types=[ec2.InstanceType("t3.medium")],  # Instance type
            min_size=1,  # Minimum number of nodes
            max_size=3,  # Maximum number of nodes
            desired_size=2,  # Desired number of nodes
        )

        # Output the cluster name and endpoint
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ClusterEndpoint", value=cluster.cluster_endpoint)

app = App()
EksClusterStack(app, "EksClusterStack")
app.synth()
