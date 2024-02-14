
import logging
import os

from dataall.core.tasks.service_handlers import Worker
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.tasks.db.task_models import Task
from dataall.modules.dataset_sharing.services.data_sharing_service import DataSharingService

log = logging.getLogger(__name__)


class EcsShareHandler:
    @staticmethod
    @Worker.handler(path='ecs.share.approve')
    def approve_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, DataSharingService.approve_share, 'approve_share')

    @staticmethod
    @Worker.handler(path='ecs.share.revoke')
    def revoke_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, DataSharingService.revoke_share, 'revoke_share')

    @staticmethod
    @Worker.handler(path='ecs.share.verify')
    def verify_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, DataSharingService.verify_share, 'verify_share')

    @staticmethod
    @Worker.handler(path='ecs.share.reapply')
    def reapply_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, DataSharingService.reapply_share, 'reapply_share')

    @staticmethod
    def _manage_share(engine, task: Task, local_handler, ecs_handler: str):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return local_handler(engine, task.targetUri)
        else:
            return EcsShareHandler._run_share_management_ecs_task(
                share_uri=task.targetUri, handler=ecs_handler
            )

    @staticmethod
    def _run_share_management_ecs_task(share_uri, handler):
        return Ecs.run_ecs_task(
            task_definition_param='ecs/task_def_arn/share_management',
            container_name_param='ecs/container/share_management',
            context=[
                {'name': 'shareUri', 'value': share_uri},
                {'name': 'handler', 'value': handler},
            ],
        )
