import os

import requests
import logging

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.stacks.aws.cloudformation import CloudFormation
from dataall.core.stacks.services.keyvaluetag_service import KeyValueTagService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.config import config
from dataall.base.context import get_context
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.stacks.db.stack_models import Stack
from dataall.core.tasks.db.task_models import Task
from dataall.base.utils import Parameter
from dataall.base.db.exceptions import AWSResourceNotFound
from dataall.base.db.exceptions import RequiredParameter
from dataall.core.stacks.db.target_type_repositories import TargetType
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.db.environment_repositories import EnvironmentRepository

log = logging.getLogger(__name__)


class StackRequestVerifier:
    @staticmethod
    def verify_get_and_describe_params(env_uri, stack_uri):
        if not env_uri:
            raise RequiredParameter('Environment URI is required')
        if not stack_uri:
            raise RequiredParameter('Stack URI is required')

    @staticmethod
    def validate_update_tag_input(data):
        if not data.get('targetUri'):
            raise ValueError('targetUri is required')

    @staticmethod
    def verify_target_type_and_uri(target_type, target_uri):
        if not target_uri:
            raise RequiredParameter('targetUri')
        if not target_type:
            raise RequiredParameter('targetType')


class StackService:
    @staticmethod
    def get_stack_with_cfn_resources(targetUri: str, environmentUri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env: Environment = EnvironmentRepository.get_environment_by_uri(session, environmentUri)
            stack: Stack = StackRepository.find_stack_by_target_uri(session, target_uri=targetUri)
            if not stack:
                stack = Stack(
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
    def create_stack(environment_uri, target_type, target_uri):
        with get_context().db_engine.scoped_session() as session:
            return StackRepository.create_stack(
                session=session,
                environment_uri=environment_uri,
                target_type=target_type,
                target_uri=target_uri,
            )

    @staticmethod
    def deploy_stack(targetUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            stack: Stack = StackRepository.get_stack_by_target_uri(session, target_uri=targetUri)
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
            stack: Stack = StackRepository.find_stack_by_target_uri(session, target_uri=target_uri)
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
    def get_stack_by_uri(stack_uri):
        with get_context().db_engine.scoped_session() as session:
            return StackRepository.get_stack_by_uri(session, stack_uri)

    @staticmethod
    def get_and_describe_stack_in_env(env: Environment, stack_uri):
        StackRequestVerifier.verify_get_and_describe_params(env.environmentUri, stack_uri)
        stack: Stack = StackService.get_stack_by_uri(stack_uri)
        with get_context().db_engine.scoped_session() as session:
            cfn_task = StackService.save_describe_stack_task(session, env, stack, None)
            CloudFormation.describe_stack_resources(engine=get_context().db_engine, task=cfn_task)
        return stack

    @staticmethod
    def update_stack_by_target_uri(target_uri, target_type):
        StackRequestVerifier.verify_target_type_and_uri(target_uri, target_type)
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=target_uri,
                permission_name=TargetType.get_resource_update_permission_name(target_type),
            )
            stack = StackRepository.get_stack_by_target_uri(session, target_uri=target_uri)
            StackService.deploy_stack(stack.targetUri)
            return stack

    @staticmethod
    def update_stack_tags(input):
        StackRequestVerifier.validate_update_tag_input(input)
        target_uri = input.get('targetUri')
        kv_tags = KeyValueTagService.update_key_value_tags(
            uri=target_uri,
            data=input,
        )
        StackService.deploy_stack(targetUri=target_uri)
        return kv_tags

    @staticmethod
    def get_stack_logs(target_uri, target_type):
        context = get_context()
        StackRequestVerifier.verify_target_type_and_uri(target_uri, target_type)

        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=target_uri,
                permission_name=TargetType.get_resource_read_permission_name(target_type),
            )
            stack = StackRepository.get_stack_by_target_uri(session, target_uri)

        if not stack.EcsTaskArn:
            raise AWSResourceNotFound(
                action='GET_STACK_LOGS',
                message='Logs could not be found for this stack',
            )

        log.info(f'Get stack Logs for stack {stack.name}')

        query = f"""fields @timestamp, @message, @logStream, @log as @logGroup
                    | sort @timestamp asc
                    | filter @logStream like "{stack.EcsTaskArn.split('/')[-1]}"
                    """
        return query
