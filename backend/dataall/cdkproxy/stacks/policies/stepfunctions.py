from aws_cdk import aws_iam as aws_iam

from .service_policy import ServicePolicy


class StepFunctions(ServicePolicy):
    def get_statements(self):
        return [
            aws_iam.PolicyStatement(
                sid='ListMonitorStepFunctions',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'states:SendTaskSuccess',
                    'states:ListStateMachines',
                    'states:SendTaskFailure',
                    'states:ListActivities',
                    'states:SendTaskHeartbeat',
                ],
                resources=['*'],
            ),
            aws_iam.PolicyStatement(
                sid='ManageTeamStepFunctions',
                effect=aws_iam.Effect.ALLOW,
                actions=['states:*'],
                resources=[
                    f'arn:aws:states:{self.region}:{self.account}:execution:{self.resource_prefix}:*',
                    f'arn:aws:states:{self.region}:{self.account}:activity:{self.resource_prefix}',
                    f'arn:aws:states:{self.region}:{self.account}:stateMachine:{self.resource_prefix}',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
        ]
