import logging
import os
import time


from backend.short_async_tasks import Worker
from ... import db
from ...db import models
from ...utils import Parameter
from ...tasks.data_sharing.data_sharing_service import DataSharingService

log = logging.getLogger('aws:ecs')

##TODO: import ECS run task only and here only redirecting to ECS long running task
@Worker.handler(path='ecs.share.approve')
def approve_share(engine, task: models.Task):
    envname = os.environ.get('envname', 'local')
    if envname in ['local', 'dkrcompose']:
        return DataSharingService.approve_share(engine, task.targetUri)
    else:
        return Ecs.run_share_management_ecs_task(
            envname, task.targetUri, 'approve_share'
        )

@Worker.handler(path='ecs.share.reject')
def reject_share(engine, task: models.Task):
    envname = os.environ.get('envname', 'local')
    if envname in ['local', 'dkrcompose']:
        return DataSharingService.reject_share(engine, task.targetUri)
    else:
        return Ecs.run_share_management_ecs_task(
            envname, task.targetUri, 'reject_share'
        )

@Worker.handler(path='ecs.cdkproxy.deploy')
def deploy_stack(engine, task: models.Task):
    with engine.scoped_session() as session:
        stack: models.Stack = db.api.Stack.get_stack_by_uri(
            session, stack_uri=task.targetUri
        )
        envname = os.environ.get('envname', 'local')
        cluster_name = Parameter().get_parameter(
            env=envname, path='ecs/cluster/name'
        )

        while Ecs.is_task_running(cluster_name, f'awsworker-{task.targetUri}'):
            log.info(
                f'ECS task for stack stack-{task.targetUri} is running waiting for 30 seconds before retrying...'
            )
            time.sleep(30)

        stack.EcsTaskArn = Ecs.run_cdkproxy_task(task.targetUri)

