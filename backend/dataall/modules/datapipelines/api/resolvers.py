import json
import logging

from dataall.aws.handlers import stepfunction as helpers
from dataall.aws.handlers.service_handlers import Worker
from dataall.api.Objects.Stack import stack_helper
from dataall.api.constants import DataPipelineRole
from dataall.api.context import Context
from dataall.core.permission_checker import has_resource_permission
from dataall.db import models
from dataall.db.api import Environment, Stack
from dataall.modules.datapipelines.services.datapipelines_service import DataPipelineService
from dataall.modules.datapipelines.db.models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository
from dataall.modules.datapipelines.services.datapipelines_permissions import START_PIPELINE

log = logging.getLogger(__name__)


def create_pipeline(context: Context, source, input=None):
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
        DataPipelineService.get_pipeline(
            session=session,
            uri=input['DataPipelineUri'],
        )
        task = models.Task(
            action='repo.datapipeline.cat',
            targetUri=input.get('DataPipelineUri'),
            payload={
                'absolutePath': input.get('absolutePath'),
                'branch': input.get('branch', 'master'),
            },
        )
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )
    return response[0]['response'].decode('ascii')


def ls(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        DataPipelineService.get_pipeline(
            session=session,
            uri=input['DataPipelineUri'],
        )
        task = models.Task(
            action='repo.datapipeline.ls',
            targetUri=input.get('DataPipelineUri'),
            payload={
                'folderPath': input.get('folderPath', '/'),
                'branch': input.get('branch', 'master'),
            },
        )
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )
    return json.dumps(response[0]['response'])


def list_branches(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        DataPipelineService.get_pipeline(
            session=session,
            uri=DataPipelineUri,
        )
        task = models.Task(action='repo.datapipeline.branches', targetUri=DataPipelineUri)
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )
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
        task = models.Task(targetUri=source.DataPipelineUri, action='glue.job.runs')
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )[0]
    return response['response']


def get_pipeline_executions(context: Context, source: DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        task = models.Task(
            targetUri=source.DataPipelineUri, action='datapipeline.pipeline.executions'
        )
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )[0]
    return response['response']


def get_creds(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return DataPipelineService.get_credentials(
            session=session,
            uri=DataPipelineUri
        )


def list_pipeline_state_machine_executions(
    context: Context, source, DataPipelineUri: str = None, stage: str = None
):
    with context.engine.scoped_session() as session:
        pipeline = DataPipelineService.get_pipeline(
            session=session,
            uri=DataPipelineUri,
        )

        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        executions = helpers.list_executions(
            state_machine_name=pipeline.name, env=env, stage='Prod'
        )

    return {
        'count': len(executions),
        'page': 1,
        'pages': 4,
        'hasNext': False,
        'hasPrevious': False,
        'nodes': executions,
    }

# TODO: double-check, but seems to be dead code
# also helpers.run_pipeline only used here
# also START_PIPELINE permission only used here
@has_resource_permission(START_PIPELINE)
def start_pipeline(context: Context, source, uri: str = None):
    with context.engine.scoped_session() as session:
        pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)

        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        execution_arn = helpers.run_pipeline(state_machine_name=pipeline.name, env=env)

    return execution_arn


def delete_pipeline(
    context: Context, source, DataPipelineUri: str = None, deleteFromAWS: bool = None
):
    with context.engine.scoped_session() as session:
        pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(
            session, DataPipelineUri
        )
        env: models.Environment = Environment.get_environment_by_uri(
            session, pipeline.environmentUri
        )
    
        DataPipelineService.delete_pipeline(
            session=session,
            uri=DataPipelineUri,
            pipeline=pipeline
        )

    if deleteFromAWS:
        stack_helper.delete_repository(
            target_uri=DataPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            repo_name=pipeline.repo,
        )
        if pipeline.devStrategy == "cdk-trunk":
            stack_helper.delete_stack(
                target_uri=DataPipelineUri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region,
            )
        else:
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
