import os

import requests

from dataall.core.stacks.aws.cloudwatch import CloudWatch
from dataall.core.tasks.service_handlers import Worker
from dataall.base.config import config
from dataall.base.context import get_context
from dataall.core.environment.db.environment_models import Environment
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.core.stacks.db.stack_models import Stack as StackModel
from dataall.core.tasks.db.task_models import Task
from dataall.base.utils import Parameter
from dataall.base.db import exceptions
from dataall.core.stacks.db.target_type_repositories import TargetType
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)


import logging

log = logging.getLogger(__name__)


class StackService:
    @staticmethod
    def get_stack_with_cfn_resources(targetUri: str, environmentUri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env: Environment = session.query(Environment).get(environmentUri)
            stack: StackModel = Stack.find_stack_by_target_uri(session, target_uri=targetUri)
            if not stack:
                stack = StackModel(
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

            cfn_task = StackService.save_describe_stack_task(session, env, stack, targetUri)
            Worker.queue(engine=context.db_engine, task_ids=[cfn_task.taskUri])
        return stack

    @staticmethod
    def save_describe_stack_task(session, environment, stack, target_uri):
        cfn_task = Task(
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

    @staticmethod
    def deploy_stack(targetUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            stack: StackModel = Stack.get_stack_by_target_uri(session, target_uri=targetUri)
            envname = os.getenv('envname', 'local')

            if envname in ['local', 'pytest', 'dkrcompose']:
                requests.post(f'{config.get_property("cdk_proxy_url")}/stack/{stack.stackUri}')

            else:
                cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
                if not Ecs.is_task_running(cluster_name, f'awsworker-{stack.stackUri}'):
                    stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack.stackUri)
                else:
                    task: Task = Task(action='ecs.cdkproxy.deploy', targetUri=stack.stackUri)
                    session.add(task)
                    session.commit()
                    Worker.queue(engine=context.db_engine, task_ids=[task.taskUri])

            return stack

    @staticmethod
    def delete_stack(target_uri, accountid, cdk_role_arn, region):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            stack: StackModel = Stack.find_stack_by_target_uri(session, target_uri=target_uri)
            if not stack:
                return
            task = Task(
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

        Worker.queue(context.db_engine, [task.taskUri])
        return True

    @staticmethod
    def get_stack_logs(session, stackUri):
        stack = Stack.find_stack_by_target_uri(session, target_uri=stackUri)
        if not stack.EcsTaskArn:
            raise exceptions.AWSResourceNotFound(
                action='GET_STACK_LOGS',
                message='Logs could not be found for this stack',
            )

        query = f"""fields @timestamp, @message, @logStream, @log as @logGroup
                    | sort @timestamp asc
                    | filter @logStream like "{stack.EcsTaskArn.split('/')[-1]}"
                    """
        envname = os.getenv('envname', 'local')
        results = CloudWatch.run_query(
            query=query,
            log_group_name=f"/{Parameter().get_parameter(env=envname, path='resourcePrefix')}/{envname}/ecs/cdkproxy",
            days=1,
        )
        log.info(f'Running Logs query {query}')
        return results

    @staticmethod
    def update_stack(session, targetUri, targetType, username, groups):
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=groups,
            resource_uri=targetUri,
            permission_name=TargetType.get_resource_update_permission_name(targetType),
        )

        stack = Stack.get_stack_by_target_uri(session, target_uri=targetUri)
        return stack

    @staticmethod
    def create_stack(session, environment_uri, target_label, target_uri, target_type, payload=None) -> StackModel:
        environment: Environment = session.query(Environment).get(environment_uri)
        if not environment:
            raise exceptions.ObjectNotFound('Environment', environment_uri)

        stack = StackModel(
            targetUri=target_uri,
            accountid=environment.AwsAccountId,
            region=environment.region,
            stack=target_type,
            payload=payload,
            name=NamingConventionService(
                target_label=target_type,
                target_uri=target_uri,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name(),
        )
        session.add(stack)
        session.commit()
        return stack
