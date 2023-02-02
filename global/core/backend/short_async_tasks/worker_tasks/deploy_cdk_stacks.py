import logging
import os


from backend.short_async_tasks import Worker
from backend.utils.aws import Ecs
from ...db import models
from ...utils import Parameter

log = logging.getLogger('aws:ecs')

##TODO: imake a better routing to long tasks, this piece between 17 and 27 could be an ECSRunner class


@staticmethod
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


@staticmethod
def run_cdkproxy_task(stack_uri):
    envname = os.environ.get('envname', 'local')
    cdkproxy_task_definition = Parameter().get_parameter(
        env=envname, path='ecs/task_def_arn/cdkproxy'
    )
    container_name = Parameter().get_parameter(
        env=envname, path='ecs/container/cdkproxy'
    )
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    subnets = Parameter().get_parameter(env=envname, path='ecs/private_subnets')
    security_groups = Parameter().get_parameter(
        env=envname, path='ecs/security_groups'
    )
    try:
        task_arn = Ecs.run_ecs_task(
            cluster_name,
            cdkproxy_task_definition,
            container_name,
            security_groups,
            subnets,
            [
                {'name': 'stackUri', 'value': stack_uri},
                {'name': 'envname', 'value': envname},
                {
                    'name': 'AWS_REGION',
                    'value': os.getenv('AWS_REGION', 'eu-west-1'),
                },
            ],
            f'awsworker-{stack_uri}',
        )
        log.info(f'ECS Task {task_arn} running')
        return task_arn
    except ClientError as e:
        log.error(e)
        raise e

