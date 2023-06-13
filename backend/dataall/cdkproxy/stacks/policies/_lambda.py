from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Lambda(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                actions=[
                    'lambda:ListFunctions',
                    'lambda:ListEventSourceMappings',
                    'lambda:ListLayerVersions',
                    'lambda:ListLayers',
                    'lambda:GetAccountSettings',
                    'lambda:CreateEventSourceMapping',
                    'lambda:ListCodeSigningConfigs',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                actions=[
                    'lambda:*',
                ],
                resources=[
                    f'arn:aws:lambda:{self.region}:{self.account}:code-signing-config:*',
                    f'arn:aws:lambda:{self.region}:{self.account}:event-source-mapping:*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:function:{self.resource_prefix}*:*',
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*',
                    f'arn:aws:lambda:{self.region}:{self.account}:layer:{self.resource_prefix}*:*',
                ],
            ),
            iam.PolicyStatement(
                sid="LoggingLambda",
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
