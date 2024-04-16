import json
import logging
import os

from dataall.base.api.context import Context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.keyvaluetag_service import KeyValueTagService
from dataall.core.stacks.services.stack_service import StackService
from dataall.core.stacks.db.stack_models import Stack
from dataall.core.stacks.aws.cloudwatch import CloudWatch
from dataall.base.utils import Parameter


log = logging.getLogger(__name__)


def get_stack(context: Context, source, environmentUri: str = None, stackUri: str = None):
    env = EnvironmentService.find_environment_by_uri(uri=environmentUri)
    return StackService.get_and_describe_stack_in_env(env, stackUri)


def resolve_link(context, source, **kwargs):
    if not source:
        return None
    return f'https://{source.region}.console.aws.amazon.com/cloudformation/home?region={source.region}#/stacks/stackinfo?stackId={source.stackid}'


def resolve_outputs(context, source: Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.outputs or {})


def resolve_resources(context, source: Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.resources or {})


def resolve_error(context, source: Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.error or {})


def resolve_events(context, source: Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.events or {})


def resolve_task_id(context, source: Stack, **kwargs):
    if not source:
        return None
    if source.EcsTaskArn:
        return source.EcsTaskArn.split('/')[-1]


def get_stack_logs(context: Context, source, targetUri: str = None, targetType: str = None):
    query=StackService.get_stack_logs(target_uri=targetUri, target_type=targetType)
    envname = os.getenv('envname', 'local')
    log_group_name = f"/{Parameter().get_parameter(env=envname, path='resourcePrefix')}/{envname}/ecs/cdkproxy"
    results = CloudWatch.run_query(
        query=query,
        log_group_name=log_group_name,
        days=1,
    )
    log.info(f'Running Logs query {query} for log_group_name={log_group_name}')
    return results


def update_stack(context: Context, source, targetUri: str = None, targetType: str = None):
    return StackService.update_stack_by_target_uri(targetUri, targetType)


def list_key_value_tags(context: Context, source, targetUri: str = None, targetType: str = None):
    return KeyValueTagService.list_key_value_tags(targetUri, targetType)


def update_key_value_tags(context: Context, source, input=None):
    return StackService.update_stack_tags(input)
