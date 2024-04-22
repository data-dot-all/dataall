from aws_cdk import aws_iam as aws_iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.modules.datapipelines.services.datapipelines_permissions import CREATE_PIPELINE


class StepFunctions(ServicePolicy):
    """
    Class including all permissions needed to work with AWS Step Functions.
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_PIPELINE not in group_permissions:
            return []

        return [
            aws_iam.PolicyStatement(
                # sid='ListMonitorStepFunctions',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'states:ListStateMachines',
                    'states:ListActivities',
                    'states:SendTaskFailure',
                    'states:SendTaskSuccess',
                    'states:SendTaskHeartbeat',
                ],
                resources=['*'],
            ),
            aws_iam.PolicyStatement(
                # sid='CreateTeamStepFunctions',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'states:CreateStateMachine',
                    'states:UpdateStateMachine',
                    'states:CreateActivity',
                    'states:TagResource',
                ],
                resources=[
                    f'arn:aws:states:{self.region}:{self.account}:stateMachine:{self.resource_prefix}*',
                    f'arn:aws:states:{self.region}:{self.account}:activity:{self.resource_prefix}*',
                ],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
            aws_iam.PolicyStatement(
                # sid='ManageTeamStepFunctions',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'states:Delete*',
                    'states:Describe*',
                    'states:Get*',
                    'states:List*',
                    'states:Start*',
                    'states:StopExecution',
                ],
                resources=[
                    f'arn:aws:states:{self.region}:{self.account}:execution:{self.resource_prefix}*:*',
                    f'arn:aws:states:{self.region}:{self.account}:activity:{self.resource_prefix}*',
                    f'arn:aws:states:{self.region}:{self.account}:stateMachine:{self.resource_prefix}*',
                ],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
        ]
