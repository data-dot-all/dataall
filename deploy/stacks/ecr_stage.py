from aws_cdk import Stage, Tags, Aspects
from cdk_nag import AwsSolutionsChecks

from .ecr_stack import ECRRepositoryStack


class ECRStage(Stage):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        tooling_account_id=None,
        target_envs=None,
        repository_name='dataall-repository',
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        ecr_stack = ECRRepositoryStack(
            self,
            f'{envname}-ecr-stack',
            target_envs=target_envs,
            envname=envname,
            resource_prefix=resource_prefix,
            repository_name=repository_name,
        )

        Tags.of(ecr_stack).add('Application', f'{resource_prefix}-{envname}')

        Aspects.of(ecr_stack).add(AwsSolutionsChecks(reports=True, verbose=True))
