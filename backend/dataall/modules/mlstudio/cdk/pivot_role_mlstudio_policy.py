from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class MLStudioPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SageMaker.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='SageMakerDomainActions',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:ListTags',
                    'sagemaker:DescribeUserProfile',
                    'sagemaker:AddTags',
                    'sagemaker:DescribeDomain',
                    'sagemaker:CreatePresignedDomainUrl',
                ],
                resources=[
                    f'arn:aws:sagemaker:*:{self.account}:domain/*',
                    f'arn:aws:sagemaker:*:{self.account}:user-profile/*/*',
                ],
            ),
            iam.PolicyStatement(
                sid='SageMakerDomainsAppsList',
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:ListDomains', 'sagemaker:ListApps'],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='EC2SGMLStudio',
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
