from aws_cdk import aws_iam as iam

from dataall.base.cdkproxy.stacks.policies.service_policy import ServicePolicy
from dataall.modules.datapipelines.services.datapipelines_permissions import CREATE_PIPELINE


class StepFunctions(ServicePolicy):
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_PIPELINE not in group_permissions:
            return []

        return [
            iam.PolicyStatement(
                actions=[
                    'states:SendTaskSuccess',
                    'states:ListStateMachines',
                    'states:SendTaskFailure',
                    'states:ListActivities',
                    'states:SendTaskHeartbeat',
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW,
            ),
            iam.PolicyStatement(
                actions=['states:*'],
                resources=[
                    f'arn:aws:states:{self.region}:{self.account}:execution:{self.resource_prefix}:*',
                    f'arn:aws:states:{self.region}:{self.account}:activity:{self.resource_prefix}',
                    f'arn:aws:states:{self.region}:{self.account}:stateMachine:{self.resource_prefix}',
                ],
                effect=iam.Effect.ALLOW,
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
        ]
