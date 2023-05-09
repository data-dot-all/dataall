
import logging
import os

from botocore.exceptions import ClientError

from dataall.aws.handlers.ecs import Ecs
from dataall.db import models
from dataall.utils import Parameter
from dataall.aws.handlers.service_handlers import Worker
from dataall.modules.dataset_sharing.services.data_sharing_service import DataSharingService

log = logging.getLogger(__name__)


class EcsShareHandler:
    @staticmethod
    @Worker.handler(path='ecs.share.approve')
    def approve_share(engine, task: models.Task):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return DataSharingService.approve_share(engine, task.targetUri)
        else:
            return EcsShareHandler.run_share_management_ecs_task(
                envname=envname, share_uri=task.targetUri, handler='approve_share'
            )

    @staticmethod
    @Worker.handler(path='ecs.share.revoke')
    def revoke_share(engine, task: models.Task):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return DataSharingService.revoke_share(engine, task.targetUri)
        else:
            return EcsShareHandler.run_share_management_ecs_task(
                envname=envname, share_uri=task.targetUri, handler='revoke_share'
            )

    @staticmethod
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
                cluster_name=cluster_name,
                task_definition=share_task_definition,
                container_name=container_name,
                security_groups=security_groups,
                subnets=subnets,
                environment=[
                    {'name': 'shareUri', 'value': share_uri},
                    {'name': 'config_location', 'value': '/config.json'},
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
