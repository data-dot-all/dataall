import logging
import os


from backend.short_async_tasks import Worker
from backend.utils.aws import Ecs
from ...db import models
from ...utils import Parameter
from ...tasks.data_sharing.data_sharing_service import DataSharingService

log = logging.getLogger('aws:ecs')

##TODO: imake a better routing to long tasks, this piece between 17 and 27 could be an ECSRunner class


def run_share_management_ecs_task(envname, share_uri, handler):
    share_task_definition = Parameter().get_parameter(
        env=envname, path='ecs/task_def_arn/share_management'
    )
    container_name = Parameter().get_parameter(
        env=envname, path='ecs/container/share_management'
    )
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    subnets = Parameter().get_parameter(env=envname, path='ecs/private_subnets')
    security_groups = Parameter().get_parameter(
        env=envname, path='ecs/security_groups'
    )

    try:
        Ecs.run_ecs_task(
            cluster_name,
            share_task_definition,
            container_name,
            security_groups,
            subnets,
            [
                {'name': 'shareUri', 'value': share_uri},
                {'name': 'envname', 'value': envname},
                {'name': 'handler', 'value': handler},
                {
                    'name': 'AWS_REGION',
                    'value': os.getenv('AWS_REGION', 'eu-west-1'),
                },
            ],
        )
        return True
    except ClientError as e:
        log.error(e)
        raise e


@Worker.handler(path='ecs.share.approve')
def approve_share(engine, task: models.Task):
    envname = os.environ.get('envname', 'local')
    if envname in ['local', 'dkrcompose']:
        return DataSharingService.approve_share(engine, task.targetUri)
    else:
        return run_share_management_ecs_task(
            envname, task.targetUri, 'approve_share'
        )


@Worker.handler(path='ecs.share.reject')
def reject_share(engine, task: models.Task):
    envname = os.environ.get('envname', 'local')
    if envname in ['local', 'dkrcompose']:
        return DataSharingService.reject_share(engine, task.targetUri)
    else:
        return run_share_management_ecs_task(
            envname, task.targetUri, 'reject_share'
        )


