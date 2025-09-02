import json
import logging
import os

from dataall.core.tasks.service_handlers import Worker
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.tasks.db.task_models import Task
from dataall.modules.shares_base.services.sharing_service import SharingService
from dataall.modules.shares_base.tasks.share_reapplier_task import EcsBulkShareRepplyService

log = logging.getLogger(__name__)


class EcsShareHandler:
    @staticmethod
    @Worker.handler(path='ecs.share.approve')
    def approve_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, SharingService.approve_share, 'approve_share')

    @staticmethod
    @Worker.handler(path='ecs.share.revoke')
    def revoke_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, SharingService.revoke_share, 'revoke_share')

    @staticmethod
    @Worker.handler(path='ecs.share.verify')
    def verify_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, SharingService.verify_share, 'verify_share')

    @staticmethod
    @Worker.handler(path='ecs.share.reapply')
    def reapply_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, SharingService.reapply_share, 'reapply_share')

    @staticmethod
    @Worker.handler(path='ecs.share.cleanup')
    def cleanup_share(engine, task: Task):
        return EcsShareHandler._manage_share(engine, task, SharingService.cleanup_share, 'cleanup_share')

    @staticmethod
    @Worker.handler(path='ecs.dataset.share.reapply')
    def reapply_shares_of_dataset(engine, task: Task):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            EcsBulkShareRepplyService.process_reapply_shares_for_dataset(engine, task.targetUri)
        else:
            context = [
                {'name': 'datasetUri', 'value': task.targetUri},
            ]
            return EcsShareHandler._run_share_management_ecs_task(
                task_definition_param_str='ecs/task_def_arn/share_reapplier',
                container_name_param_str='ecs/container/share_reapplier',
                context=context,
            )

    @staticmethod
    def _manage_share(engine, task: Task, local_handler, ecs_handler: str):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return local_handler(engine, task.targetUri)
        else:
            share_management_context = [
                {'name': 'shareUri', 'value': task.targetUri},
                {'name': 'handler', 'value': ecs_handler},
            ]
            return EcsShareHandler._run_share_management_ecs_task(
                task_definition_param_str='ecs/task_def_arn/share_management',
                container_name_param_str='ecs/container/share_management',
                context=share_management_context,
            )

    @staticmethod
    def _run_share_management_ecs_task(task_definition_param_str, container_name_param_str, context):
        ecs_task_arn = Ecs.run_ecs_task(
            task_definition_param=task_definition_param_str,
            container_name_param=container_name_param_str,
            context=context,
        )
        return {'task_arn': ecs_task_arn}
