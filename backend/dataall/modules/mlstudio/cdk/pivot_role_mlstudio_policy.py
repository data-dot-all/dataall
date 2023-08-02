from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class MLStudioPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SageMaker.
    It allows pivot role to:
    - ....
    """
    # TODO: remove notebooks permissions
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='SageMakerNotebookActions',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:ListTags',
                    'sagemaker:DescribeUserProfile',
                    'sagemaker:StopNotebookInstance',
                    'sagemaker:CreatePresignedNotebookInstanceUrl',
                    'sagemaker:DescribeNotebookInstance',
                    'sagemaker:StartNotebookInstance',
                    'sagemaker:AddTags',
                    'sagemaker:DescribeDomain',
                    'sagemaker:CreatePresignedDomainUrl',
                ],
                resources=[
                    f'arn:aws:sagemaker:*:{self.account}:notebook-instance/{self.env_resource_prefix}*',
                    f'arn:aws:sagemaker:*:{self.account}:domain/*',
                    f'arn:aws:sagemaker:*:{self.account}:user-profile/*/*',
                ],
            ),
            iam.PolicyStatement(
                sid='SageMakerNotebookInstances',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:ListNotebookInstances',
                    'sagemaker:ListDomains',
                    'sagemaker:ListApps',
                    'sagemaker:DeleteApp',
                ],
                resources=['*'],
            ),
        ]
        return statements
