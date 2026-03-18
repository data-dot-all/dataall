import jsii
from aws_cdk import IAspect, CfnResource


@jsii.implements(IAspect)
class PermissionsBoundaryAspect:
    """CDK Aspect that applies a permissions boundary to all IAM roles in a stack.

    This handles roles auto-created by CDK constructs (e.g. cr.Provider, BucketDeployment)
    that cannot be configured directly.
    """

    def __init__(self, permissions_boundary_arn: str):
        self._arn = permissions_boundary_arn

    def visit(self, node):
        if isinstance(node, CfnResource) and node.cfn_resource_type == 'AWS::IAM::Role':
            node.add_property_override('PermissionsBoundary', self._arn)
