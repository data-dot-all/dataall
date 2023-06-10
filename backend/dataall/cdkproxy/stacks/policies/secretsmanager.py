from .service_policy import ServicePolicy
from aws_cdk import aws_iam


class SecretsManager(ServicePolicy):

    def get_statements(self):
        statements = [
            aws_iam.PolicyStatement(
                sid="SecretsReadAll",
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:ListSecrets",
                ],
                resources=["*"],
            ),
            aws_iam.PolicyStatement(
                sid='ManageTeamSecrets',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'secretsmanager:DescribeSecret',
                    'secretsmanager:GetSecretValue',
                    'secretsmanager:CreateSecret',
                    'secretsmanager:DeleteSecret',
                    'secretsmanager:TagResource',
                ],
                resources=['*'],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            )
        ]
        return statements
