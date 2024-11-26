import os

import requests
import logging

from dataall.base.db import exceptions
from dataall.base.feature_toggle_checker import is_feature_enabled_for_allowed_values
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
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


def map_target_type_to_log_config_path(**kwargs):
    target_type = kwargs.get('target_type')
    if target_type == 'environment':
        return 'core.features.show_stack_logs'
    elif target_type == 'dataset':
        return 'modules.s3_datasets.features.show_stack_logs'
    elif target_type == 'mlstudio':
        return 'modules.mlstudio.features.show_stack_logs'
    elif target_type == 'notebooks':
        return 'modules.notebooks.features.show_stack_logs'
    elif target_type == 'datapipelines':
        return 'modules.datapipelines.features.show_stack_logs'
    else:
        return 'Invalid Config'


class StackService:
    @staticmethod
    def resolve_parent_obj_stack(targetUri: str, targetType: str, environmentUri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=targetUri,
                permission_name=TargetType.get_resource_read_permission_name(targetType),
            )
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
    def get_and_describe_stack_in_env(env: Environment, stack_uri, target_uri, target_type):
        StackRequestVerifier.verify_get_and_describe_params(env.environmentUri, stack_uri)
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=target_uri,
                permission_name=TargetType.get_resource_read_permission_name(target_type),
            )
            stack: Stack = StackRepository.get_stack_by_uri(session, stack_uri)

            cfn_task = StackService.save_describe_stack_task(session, env, stack, None)
            CloudFormation.describe_stack_resources(engine=get_context().db_engine, task=cfn_task)
        return stack

    @staticmethod
    def update_stack_by_target_uri(target_uri, target_type):
        StackRequestVerifier.verify_target_type_and_uri(target_uri, target_type)
        context = get_context()
        with context.db_engine.scoped_session() as session:
            TenantPolicyService.check_user_tenant_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                permission_name=TargetType.get_resource_tenant_permission_name(target_type),
                tenant_name=TenantPolicyService.TENANT_NAME,
            )
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
        target_type = input.get('targetType')
        context = get_context()
        with context.db_engine.scoped_session() as session:
            TenantPolicyService.check_user_tenant_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                permission_name=TargetType.get_resource_tenant_permission_name(target_type),
                tenant_name=TenantPolicyService.TENANT_NAME,
            )
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=target_uri,
                permission_name=TargetType.get_resource_update_permission_name(target_type),
            )
        kv_tags = KeyValueTagService.update_key_value_tags(
            uri=target_uri,
            data=input,
        )
        StackService.deploy_stack(targetUri=target_uri)
        return kv_tags

    @staticmethod
    def get_stack_logs(target_uri, target_type):
        context = get_context()
        StackService.check_if_user_allowed_view_logs(target_type=target_type, target_uri=target_uri)
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

    @staticmethod
    @is_feature_enabled_for_allowed_values(
        allowed_values=['admin-only', 'enabled', 'disabled'],
        enabled_values=['admin-only', 'enabled'],
        default_value='enabled',
        resolve_property=map_target_type_to_log_config_path,
    )
    def check_if_user_allowed_view_logs(target_type: str, target_uri: str):
        context = get_context()
        config_value = config.get_property(map_target_type_to_log_config_path(target_type=target_type), 'enabled')
        if config_value == 'admin-only' and 'DAAdministrators' not in context.groups:
            raise exceptions.ResourceUnauthorized(
                username=context.username,
                action='View Stack logs',
                resource_uri=f'{target_uri} ( Resource type: {target_type} )',
            )
        return True
