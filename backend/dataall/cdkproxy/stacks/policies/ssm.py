from .service_policy import ServicePolicy
from aws_cdk import aws_iam


class SSM(ServicePolicy):

    def get_statements(self):
        statements = [
            aws_iam.PolicyStatement(
                sid="SSMReadAll",
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "ssm:DescribeParameters",
                ],
                resources=["*"],
            ),
            aws_iam.PolicyStatement(
                sid='ManageTeamParameters',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'ssm:PutParameter',
                    'ssm:DeleteParameter',
                    'ssm:GetParameterHistory',
                    'ssm:GetParametersByPath',
                    'ssm:GetParameters',
                    'ssm:GetParameter',
                    'ssm:DeleteParameters',
                    'ssm:AddTagsToResource',
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
