import json
import logging
import os

from dataall.base.api.context import Context
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.stack_service import StackService
from dataall.core.stacks.aws.cloudformation import CloudFormation
from dataall.core.stacks.aws.cloudwatch import CloudWatch
from dataall.core.stacks.db.stack_models import Stack as StackModel
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.base.db import exceptions
from dataall.base.utils import Parameter

log = logging.getLogger(__name__)


def get_stack(context: Context, source, environmentUri: str = None, stackUri: str = None):
    with context.engine.scoped_session() as session:
        env: Environment = session.query(Environment).get(environmentUri)
        stack: StackModel = session.query(StackModel).get(stackUri)
        cfn_task = StackService.save_describe_stack_task(session, env, stack, None)
        CloudFormation.describe_stack_resources(engine=context.engine, task=cfn_task)
        return EnvironmentService.get_stack(
            session=session,
            uri=environmentUri,
            stack_uri=stackUri,
        )


def resolve_link(context, source, **kwargs):
    if not source:
        return None
    return f'https://{source.region}.console.aws.amazon.com/cloudformation/home?region={source.region}#/stacks/stackinfo?stackId={source.stackid}'


def resolve_outputs(context, source: StackModel, **kwargs):
    if not source:
        return None
    return json.dumps(source.outputs or {})


def resolve_resources(context, source: StackModel, **kwargs):
    if not source:
        return None
    return json.dumps(source.resources or {})


def resolve_error(context, source: StackModel, **kwargs):
    if not source:
        return None
    return json.dumps(source.error or {})


def resolve_events(context, source: StackModel, **kwargs):
    if not source:
        return None
    return json.dumps(source.events or {})


def resolve_task_id(context, source: StackModel, **kwargs):
    if not source:
        return None
    if source.EcsTaskArn:
        return source.EcsTaskArn.split('/')[-1]


def get_stack_logs(context: Context, source, stackUri: str = None):
    with context.engine.scoped_session() as session:
        return StackService.get_stack_logs(session, stackUri)


def update_stack(context: Context, source, targetUri: str = None, targetType: str = None):
    if not targetUri:
        raise exceptions.RequiredParameter('targetUri')
    if not targetType:
        raise exceptions.RequiredParameter('targetType')
    with context.engine.scoped_session() as session:
        stack = StackService.update_stack(
            session=session,
            targetUri=targetUri,
            targetType=targetType,
            username=context.username,
            groups=context.groups,
        )
        StackService.deploy_stack(stack.targetUri)

    return stack


def list_key_value_tags(context: Context, source, targetUri: str = None, targetType: str = None):
    with context.engine.scoped_session() as session:
        return KeyValueTag.list_key_value_tags(
            session=session,
            uri=targetUri,
            target_type=targetType,
        )


def update_key_value_tags(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        kv_tags = KeyValueTag.update_key_value_tags(
            session=session,
            uri=input['targetUri'],
            data=input,
        )
        StackService.deploy_stack(targetUri=input['targetUri'])
        return kv_tags
