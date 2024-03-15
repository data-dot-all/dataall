from aws_cdk import Aspects, Stack
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression

CDK_NAG_EXCLUSIONS = [
    {
        'id': 'AwsSolutions-IAM5',
        'reason': 'Wildcard IAM policies are used due to the extensive read/write permission required',
    },
    {
        'id': 'AwsSolutions-IAM4',
        'reason': 'For sake of agility redefinition of IAM managed policies',
    },
    {
        'id': 'AwsSolutions-SQS2',
        'reason': 'SQS is only used for lambda functions dead letter queues with no encryption',
    },
    {
        'id': 'AwsSolutions-SQS3',
        'reason': 'SQS is only used for lambda functions dead letter queues.',
    },
    {
        'id': 'AwsSolutions-S1',
        'reason': 'Recursive s3 access logs problem',
    },
    {
        'id': 'AwsSolutions-KMS5',
        'reason': 'CDKNAG Error: KMS rotation enabled but not detected',
    },
    {
        'id': 'AwsSolutions-CB3',
        'reason': 'CB privileged mode is required to build docker images',
    },
]


class CDKNagUtil:
    def __init__(self, stack: Stack):
        self.stack = stack

    @classmethod
    def check_rules(cls, stack: Stack):
        Aspects.of(stack).add(AwsSolutionsChecks(reports=True, verbose=True))
        NagSuppressions.add_stack_suppressions(
            stack,
            suppressions=[
                NagPackSuppression(id=rule_suppressed['id'], reason=rule_suppressed['reason'])
                for rule_suppressed in CDK_NAG_EXCLUSIONS
            ],
            apply_to_nested_stacks=True,
        )
