from .service_policy import ServicePolicy
from aws_cdk import aws_iam


class SecretsManager(ServicePolicy):

    def get_statements(self):
        statements = [
            aws_iam.PolicyStatement(
                sid="SecretsReadAll",
                effect=aws_iam.Effect.ALLOW,
                actions=["secretsmanager:ListSecrets"],
                resources=["*"],
            ),
            aws_iam.PolicyStatement(
                sid='CreateTeamSecrets',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:CreateSecret",
                    "secretsmanager:DeleteSecret",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:TagResource",
                ],
                resources=[f"arn:aws:secretsmanager:*:{self.account}:secret:{self.resource_prefix}*"],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            aws_iam.PolicyStatement(
                sid='ManageTeamSecrets',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:CreateSecret",
                    "secretsmanager:DeleteSecret",
                    "secretsmanager:UpdateSecret"
                ],
                resources=[f"arn:aws:secretsmanager:*:{self.account}:secret:{self.resource_prefix}*"],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            )
        ]
        return statements
