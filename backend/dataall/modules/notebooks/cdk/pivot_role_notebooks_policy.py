from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class NotebooksPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SageMaker.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='SageMakerNotebookActions',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:ListTags',
                    'sagemaker:StopNotebookInstance',
                    'sagemaker:CreatePresignedNotebookInstanceUrl',
                    'sagemaker:DescribeNotebookInstance',
                    'sagemaker:StartNotebookInstance',
                    'sagemaker:AddTags',
                ],
                resources=[
                    f'arn:aws:sagemaker:*:{self.account}:notebook-instance/{self.env_resource_prefix}*',
                ],
            ),
            iam.PolicyStatement(
                sid='SageMakerNotebookList',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:ListNotebookInstances',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='EC2SGNotebooks',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ec2:DescribeSubnets',
                    'ec2:DescribeSecurityGroups',
                    'ec2:DescribeVpcs',
                    'ec2:DescribeInstances',
                    'ec2:DescribeNetworkInterfaces',
                ],
                resources=['*'],
            ),
        ]
        return statements
