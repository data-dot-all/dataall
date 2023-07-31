import json
import logging

from dataall.base.api.context import Context
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.environment.db.models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.db.stack import Stack
from dataall.core.tasks.db.task_models import Task
from dataall.base.db import exceptions
from dataall.modules.datapipelines.api.enums import DataPipelineRole
from dataall.modules.datapipelines.db.models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.datapipelines_repository import DatapipelinesRepository
from dataall.modules.datapipelines.services.datapipelines_service import DataPipelineService

log = logging.getLogger(__name__)


def create_pipeline(context: Context, source, input=None):
    _validate_input(input)

    with context.engine.scoped_session() as session:
        pipeline = DataPipelineService.create_pipeline(
            session=session,
            admin_group=input['SamlGroupName'],
            username=context.username,
            uri=input['environmentUri'],
            data=input,
        )
        if input['devStrategy'] == 'cdk-trunk':
            Stack.create_stack(
                session=session,
                environment_uri=pipeline.environmentUri,
                target_type='cdkpipeline',
                target_uri=pipeline.DataPipelineUri,
                target_label=pipeline.label,
                payload={'account': pipeline.AwsAccountId, 'region': pipeline.region},
            )
        else:
            Stack.create_stack(
                session=session,
                environment_uri=pipeline.environmentUri,
                target_type='pipeline',
                target_uri=pipeline.DataPipelineUri,
                target_label=pipeline.label,
                payload={'account': pipeline.AwsAccountId, 'region': pipeline.region},
            )

    stack_helper.deploy_stack(pipeline.DataPipelineUri)

    return pipeline


def create_pipeline_environment(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline_env = DataPipelineService.create_pipeline_environment(
            session=session,
            admin_group=input['samlGroupName'],
            uri=input['environmentUri'],
            username=context.username,
            data=input,
        )
    return pipeline_env


def update_pipeline(context: Context, source, DataPipelineUri: str, input: dict = None):
    with context.engine.scoped_session() as session:
        pipeline = DataPipelineService.update_pipeline(
            session=session,
            uri=DataPipelineUri,
            data=input,
        )
    if (pipeline.template == ""):
        stack_helper.deploy_stack(pipeline.DataPipelineUri)

    return pipeline


def list_pipelines(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatapipelinesRepository.paginated_user_pipelines(
            session=session,
            username=context.username,
            groups=context.groups,
            data=filter,
        )


def get_pipeline(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return DataPipelineService.get_pipeline(
            session=session,
            uri=DataPipelineUri,
        )


def resolve_user_role(context: Context, source: DataPipeline):
    if not source:
        return None
    if context.username and source.owner == context.username:
        return DataPipelineRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DataPipelineRole.Admin.value
    return DataPipelineRole.NoPermission.value


def get_pipeline_environment(context: Context, source: DataPipelineEnvironment, **kwargs):
    with context.engine.scoped_session() as session:
        return DataPipelineService.get_pipeline_environment(
            session=session,
            uri=source.envPipelineUri,
        )


def list_pipeline_environments(context: Context, source: DataPipeline, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatapipelinesRepository.paginated_pipeline_environments(
            session=session,
            uri=source.DataPipelineUri,
            data=filter
        )


def get_clone_url_http(context: Context, source: DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return DatapipelinesRepository.get_clone_url_http(
            session=session,
            environmentUri=source.environmentUri,
            repo=source.repo
        )


def cat(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        try:
            response = DataPipelineService.cat(
                session=session,
                input=input
            )
        except Exception as e:
            log.error(f"Failed to execute task due to: {e}")

        return response[0]['response'].decode('ascii')


def ls(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        try:
            response = DataPipelineService.ls(
                session=session,
                input=input
            )
        except Exception as e:
            log.error(f"Failed to execute task due to: {e}")

        return json.dumps(response[0]['response'])


def list_branches(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        try:
            response = DataPipelineService.list_branches(
                session=session,
                datapipeline_uri=DataPipelineUri
            )
        except Exception as e:
            log.error(f"Failed to execute task due to: {e}")

        return response[0]['response']


def get_stack(context, source: DataPipeline, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.DataPipelineUri,
        environmentUri=source.environmentUri,
    )


def get_job_runs(context, source: DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        try:
            response = DataPipelineService.get_job_runs(
                session=session,
                datapipeline_uri=source.DataPipelineUri
            )
        except Exception as e:
            log.error(f"Failed to execute task due to: {e}")

        return response[0]['response']


def get_pipeline_executions(context: Context, source: DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        try:
            response = DataPipelineService.get_pipeline_execution(
                session=session,
                datapipeline_uri=source.DataPipelineUri
            )
        except Exception as e:
            log.error(f"Failed to find pipeline execution for {source.DataPipelineUri}. Error {e}")

        return response[0]['response']


def get_creds(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return DataPipelineService.get_credentials(
            session=session,
            uri=DataPipelineUri
        )


def _delete_repository(
    target_uri, accountid, cdk_role_arn, region, repo_name
):
    context = get_context()
    with context.db_engine.scoped_session() as session:
        task = Task(
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
    Worker.queue(context.db_engine, [task.taskUri])

    return True


def delete_pipeline(
    context: Context, source, DataPipelineUri: str = None, deleteFromAWS: bool = None
):
    with context.engine.scoped_session() as session:
        pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(
            session, DataPipelineUri
        )
        env: Environment = EnvironmentService.get_environment_by_uri(
            session, pipeline.environmentUri
        )

        DataPipelineService.delete_pipeline(
            session=session,
            uri=DataPipelineUri,
            pipeline=pipeline
        )

    if deleteFromAWS:
        _delete_repository(
            target_uri=DataPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            repo_name=pipeline.repo,
        )
        stack_helper.delete_stack(
            target_uri=DataPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
        )

    return True


def delete_pipeline_environment(context: Context, source, envPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        DatapipelinesRepository.delete_pipeline_environment(
            session=session,
            envPipelineUri=envPipelineUri
        )
    return True


def update_pipeline_environment(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline_env = DataPipelineService.update_pipeline_environment(
            session=session,
            data=input,
            uri=input['pipelineUri'],
        )
    return pipeline_env


def _validate_input(data):
    if not data:
        raise exceptions.RequiredParameter(data)
    if not data.get('environmentUri'):
        raise exceptions.RequiredParameter('environmentUri')
    if not data.get('SamlGroupName'):
        raise exceptions.RequiredParameter('group')
    if not data.get('label'):
        raise exceptions.RequiredParameter('label')
