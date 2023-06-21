from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Lambda(ServicePolicy):
    """
    Class including all permissions needed to work with AWS Lambda.
    It allows data.all users to:
    - List Lambda resources
    - Create and manage team Lambda resources
    - Log Lambda executions
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                #sid="ListLambda",
                actions=[
                    'lambda:ListFunctions',
                    'lambda:ListEventSourceMappings',
                    'lambda:ListLayerVersions',
                    'lambda:ListLayers',
                    'lambda:GetLayer*',
                    'lambda:GetAccountSettings',
                    'lambda:GetEventSourceMapping',
                    'lambda:CreateEventSourceMapping',
                    'lambda:ListEventSourceMappings',
                    'lambda:CreateCodeSigningConfig',
                    'lambda:ListCodeSigningConfigs',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                #sid="GenericLambdaFunctions",
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
                #sid="CreateTeamLambda",
                actions=[
                    'lambda:CreateFunction',
                    'lambda:TagResource',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                #sid="ManageTeamLambda",
                actions=[
                    'lambda:CreateAlias',
                    'lambda:Delete*',
                    'lambda:Get*',
                    'lambda:Invoke*',
                    'lambda:List*',
                    'lambda:Publish*',
                    'lambda:Put*',
                    'lambda:Update*',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                #sid="ManageLambdaLayers",
                actions=[
                    'lambda:PublishLayerVersion',
                    'lambda:DeleteLayerVersion',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*:*',
                ]
            ),
            iam.PolicyStatement(
                #sid="LoggingLambda",
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
            )
        ]
        return statements
