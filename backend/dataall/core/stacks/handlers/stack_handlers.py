import logging
import os
import time

from botocore.exceptions import ClientError

from dataall.core.tasks.service_handlers import Worker
from dataall.core.stacks.aws.cloudformation import CloudFormation
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.stacks.db import stack_models as models
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.tasks.db.task_models import Task
from dataall.base.utils import Parameter

log = logging.getLogger(__name__)


class StackHandlers:
    @staticmethod
    @Worker.handler(path='cloudformation.stack.delete')
    def delete_stack(engine, task: Task):
        try:
            data = {
                'accountid': task.payload['accountid'],
                'region': task.payload['region'],
                'stack_name': task.payload['stack_name'],
            }
            CloudFormation.delete_cloudformation_stack(**data)
        except ClientError as e:
            log.error(f'Failed to delete CFN stack{task.targetUri}: {e}')
            raise e
        return {'status': 200, 'stackDeleted': True}

    @staticmethod
    @Worker.handler(path='cloudformation.stack.describe_resources')
    def describe_stack_resources(engine, task: Task):
        CloudFormation.describe_stack_resources(engine, task)

    @staticmethod
    @Worker.handler(path='ecs.cdkproxy.deploy')
    def deploy_stack(engine, task: Task):
        with engine.scoped_session() as session:
            stack: models.Stack = StackRepository.get_stack_by_uri(session, stack_uri=task.targetUri)
            envname = os.environ.get('envname', 'local')
            cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')

            while Ecs.is_task_running(cluster_name=cluster_name, started_by=f'awsworker-{task.targetUri}'):
                log.info(
                    f'ECS task for stack stack-{task.targetUri} is running waiting for 30 seconds before retrying...'
                )
                time.sleep(30)

            stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack_uri=task.targetUri)
