import json
import logging
import os

from . import stack_helper
from ...context import Context
from .... import db
from ....aws.handlers.cloudformation import CloudFormation
from ....aws.handlers.cloudwatch import CloudWatch
from ....db import exceptions
from ....db import models
from ....utils import Parameter

log = logging.getLogger(__name__)


def get_stack(
    context: Context, source, environmentUri: str = None, stackUri: str = None
):
    with context.engine.scoped_session() as session:
        env: models.Environment = session.query(models.Environment).get(environmentUri)
        stack: models.Stack = session.query(models.Stack).get(stackUri)
        cfn_task = stack_helper.save_describe_stack_task(session, env, stack, None)
        CloudFormation.describe_stack_resources(engine=context.engine, task=cfn_task)
        return db.api.Environment.get_stack(
            session=session,
            uri=environmentUri,
            stack_uri=stackUri,
        )


def resolve_link(context, source, **kwargs):
    if not source:
        return None
    return f'https://{source.region}.console.aws.amazon.com/cloudformation/home?region={source.region}#/stacks/stackinfo?stackId={source.stackid}'


def resolve_outputs(context, source: models.Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.outputs or {})


def resolve_resources(context, source: models.Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.resources or {})


def resolve_error(context, source: models.Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.error or {})


def resolve_events(context, source: models.Stack, **kwargs):
    if not source:
        return None
    return json.dumps(source.events or {})


def resolve_task_id(context, source: models.Stack, **kwargs):
    if not source:
        return None
    if source.EcsTaskArn:
        return source.EcsTaskArn.split('/')[-1]


def get_stack_logs(
    context: Context, source, environmentUri: str = None, stackUri: str = None
):
    with context.engine.scoped_session() as session:
        stack = db.api.Environment.get_stack(
            session=session,
            uri=environmentUri,
            stack_uri=stackUri
        )
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


def update_stack(
    context: Context, source, targetUri: str = None, targetType: str = None
):
    with context.engine.scoped_session() as session:
        stack = db.api.Stack.update_stack(
            session=session,
            uri=targetUri,
            target_type=targetType
        )
    stack_helper.deploy_stack(stack.targetUri)
    return stack
