from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.modules.datapipelines.services.datapipelines_permissions import CREATE_PIPELINE
from aws_cdk import aws_iam as iam


class Lambda(ServicePolicy):
    """
    Class including all permissions needed to work with AWS Lambda.
    It allows data.all users to:
    - List Lambda resources
    - Create and manage team Lambda resources
    - Log Lambda executions
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_PIPELINE not in group_permissions:
            return []

        statements = [
            iam.PolicyStatement(
                # sid="ListLambda",
                actions=[
                    'lambda:List*',
                    'lambda:GetLayer*',
                    'lambda:GetAccountSettings',
                    'lambda:GetEventSourceMapping',
                    'lambda:CreateEventSourceMapping',
                    'lambda:CreateCodeSigningConfig',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="GenericLambdaFunctions",
                actions=[
                    'lambda:UpdateFunctionCodeSigningConfig',
                    'lambda:UpdateEventSourceMapping',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*',
                    f'arn:aws:lambda:{self.region}:{self.account}:code-signing-config:*',
                    f'arn:aws:lambda:{self.region}:{self.account}:event-source-mapping:*',
                ],
            ),
            iam.PolicyStatement(
                # sid="CreateTeamLambda",
                actions=[
                    'lambda:CreateFunction',
                    'lambda:TagResource',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*',
                ],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
            iam.PolicyStatement(
                # sid="ManageTeamLambda",
                not_actions=[
                    'lambda:CreateFunction',
                    'lambda:TagResource',
                    'lambda:UntagResource',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*',
                ],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
            iam.PolicyStatement(
                # sid="ManageLambdaLayers",
                actions=[
                    'lambda:PublishLayerVersion',
                    'lambda:DeleteLayerVersion',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*:*',
                ],
            ),
            iam.PolicyStatement(
                # sid="LoggingLambda",
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*',
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*:log-stream:*',
                ],
            ),
        ]
        return statements
