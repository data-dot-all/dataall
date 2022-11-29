import os

import requests

from .... import db
from ....api.context import Context
from ....aws.handlers.service_handlers import Worker
from ....aws.handlers.ecs import Ecs
from ....db import models
from ....utils import Parameter


def get_stack_with_cfn_resources(context: Context, targetUri: str, environmentUri: str):
    with context.engine.scoped_session() as session:
        env: models.Environment = session.query(models.Environment).get(environmentUri)
        stack: models.Stack = db.api.Stack.find_stack_by_target_uri(
            session, target_uri=targetUri
        )
        if not stack:
            stack = models.Stack(
                stack='environment',
                payload={},
                targetUri=targetUri,
                accountid=env.AwsAccountId if env else 'UNKNOWN',
                region=env.region if env else 'UNKNOWN',
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
        stack: models.Stack = db.api.Stack.get_stack_by_target_uri(
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


def deploy_dataset_stack(context, dataset: models.Dataset):
    """
    Each dataset stack deployment triggers environment stack update
    to rebuild teams IAM roles data access policies
    """
    deploy_stack(context, dataset.datasetUri)
    deploy_stack(context, dataset.environmentUri)


def delete_stack(
    context, target_uri, accountid, cdk_role_arn, region, target_type=None
):
    with context.engine.scoped_session() as session:
        stack: models.Stack = db.api.Stack.find_stack_by_target_uri(
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


def delete_repository(
    context, target_uri, accountid, cdk_role_arn, region, repo_name
):
    with context.engine.scoped_session() as session:
        task = models.Task(
            targetUri=target_uri,
            action='repo.datapipeline.delete',
            payload={
                'accountid': accountid,
                'region': region,
                'cdk_role_arn': cdk_role_arn,
                'repo_name': repo_name,
            },
        )
        session.add(task)
    Worker.queue(context.engine, [task.taskUri])
    return True
