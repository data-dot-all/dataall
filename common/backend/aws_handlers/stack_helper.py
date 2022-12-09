import os

import requests


from backend.api.context import Context
from backend.aws_handlers.service_handlers import Worker
from backend.aws_handlers.ecs import Ecs
from backend.utils.parameter import Parameter
from backend.db import models, operations


def get_stack_with_cfn_resources(context: Context, targetUri: str, AwsAccountId: str, region: str):
    with context.engine.scoped_session() as session:
        stack: models.Stack = operations.Stack.find_stack_by_target_uri(
            session, target_uri=targetUri
        )
        if not stack:
            stack = models.Stack(
                stack='environment',
                payload={},
                targetUri=targetUri,
                accountid=AwsAccountId,
                region=region,
                resources=str({}),
                error=str({}),
                outputs=str({}),
            )
            return stack

        cfn_task = save_describe_stack_task(session, env, stack, targetUri)
        Worker.queue(engine=context.engine, task_ids=[cfn_task.taskUri])
    return stack


def save_describe_stack_task(session, environment, stack, target_uri):
    cfn_task = models.Task(
        targetUri=stack.stackUri,
        action='cloudformation.stack.describe_resources',
        payload={
            'accountid': environment.AwsAccountId,
            'region': environment.region,
            'role_arn': environment.CDKRoleArn,
            'stack_name': stack.name,
            'stackUri': stack.stackUri,
            'targetUri': target_uri,
        },
    )
    session.add(cfn_task)
    session.commit()
    return cfn_task


def deploy_stack(context, targetUri):
    with context.engine.scoped_session() as session:
        stack: models.Stack = operations.Stack.get_stack_by_target_uri(
            session, target_uri=targetUri
        )
        envname = os.getenv('envname', 'local')

        if envname in ['local', 'pytest', 'dkrcompose']:
            requests.post(f'{context.cdkproxyurl}/stack/{stack.stackUri}')

        else:
            cluster_name = Parameter().get_parameter(
                env=envname, path='ecs/cluster/name'
            )
            if not Ecs.is_task_running(cluster_name, f'awsworker-{stack.stackUri}'):
                stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack.stackUri)
            else:
                task: models.Task = models.Task(
                    action='ecs.cdkproxy.deploy', targetUri=stack.stackUri
                )
                session.add(task)
                session.commit()
                Worker.queue(engine=context.engine, task_ids=[task.taskUri])

        return stack


def delete_stack(
    context, target_uri, accountid, cdk_role_arn, region, target_type=None
):
    with context.engine.scoped_session() as session:
        stack: models.Stack = operations.Stack.find_stack_by_target_uri(
            session, target_uri=target_uri
        )
        if not stack:
            return
        task = models.Task(
            targetUri=target_uri,
            action='cloudformation.stack.delete',
            payload={
                'accountid': accountid,
                'region': region,
                'cdk_role_arn': cdk_role_arn,
                'stack_name': stack.name,
            },
        )
        session.add(task)

    Worker.queue(context.engine, [task.taskUri])
    return True



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