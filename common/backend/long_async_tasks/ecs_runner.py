import logging
import os


from backend.short_async_tasks import Worker
from backend.utils.aws import Ecs
from ...db import models
from ...utils import Parameter
from ...tasks.data_sharing.data_sharing_service import DataSharingService

log = logging.getLogger('aws:ecs')

##TODO: make a better routing to long tasks, this runner can serve as starting point

class EcsRunner:
    def __init__(self):
        self.task_def_arn = 'ecs/task_def_arn/'
        self.container_name = 'ecs/container/'
        self.cluster_name = 'ecs/cluster/name'
        self.subnets = 'ecs/private_subnets'
        self.security_groups = 'ecs/security_groups'

    @classmethod
    def run_task(self, envname, task):
        task_definition = Parameter().get_parameter(env=envname, path=f'{self.task_def_arn}{task}')
        container_name = Parameter().get_parameter(env=envname, path=f'{self.container_name}{task}')
        cluster_name = Parameter().get_parameter(env=envname, path=self.cluster_name)
        subnets = Parameter().get_parameter(env=envname, path=self.subnets)
        security_groups = Parameter().get_parameter(env=envname, path=self.security_groups)

        try:
            Ecs.run_ecs_task(
                cluster_name,
                task_definition,
                container_name,
                security_groups,
                subnets,
                [
                    {'name': 'envname', 'value': envname},
                    {'name': 'task', 'value': task},
                    {
                        'name': 'AWS_REGION',
                        'value': os.getenv('AWS_REGION', 'eu-west-1'),
                    },
                ],
            )
            return True
        except Exception as e:
            log.error(e)
            raise e


