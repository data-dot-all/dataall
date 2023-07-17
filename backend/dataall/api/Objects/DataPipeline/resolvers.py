import json
import logging

from ....aws.handlers import stepfunction as helpers
from ...Objects.Stack import stack_helper
from ...constants import DataPipelineRole
from ...context import Context
from ....aws.handlers.service_handlers import Worker
from ....aws.handlers.sts import SessionHelper
from ....db import permissions, models, exceptions
from ....db.api import Pipeline, Environment, ResourcePolicy, Stack, KeyValueTag

log = logging.getLogger(__name__)


def create_pipeline(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.create_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['environmentUri'],
            data=input,
            check_perm=True,
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

    stack_helper.deploy_stack(context, pipeline.DataPipelineUri)

    return pipeline


def create_pipeline_environment(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline_env = Pipeline.create_pipeline_environment(
            session=session,
            username=context.username,
            groups=context.groups,
            data=input,
            check_perm=True,
        )
    return pipeline_env


def update_pipeline(context: Context, source, DataPipelineUri: str, input: dict = None):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.update_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=DataPipelineUri,
            data=input,
            check_perm=True,
        )
    if (pipeline.template == ""):
        stack_helper.deploy_stack(context, pipeline.DataPipelineUri)

    return pipeline


def list_pipelines(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Pipeline.paginated_user_pipelines(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=None,
        )


def get_pipeline(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=DataPipelineUri,
            data=None,
            check_perm=True,
        )


def get_pipeline_env(context: Context, source: models.DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env = session.query(models.Environment).get(source.environmentUri)
    return env


def resolve_user_role(context: Context, source: models.DataPipeline):
    if not source:
        return None
    if context.username and source.owner == context.username:
        return DataPipelineRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DataPipelineRole.Admin.value
    return DataPipelineRole.NoPermission.value


def get_pipeline_environment(context: Context, source: models.DataPipelineEnvironment, **kwargs):
    with context.engine.scoped_session() as session:
        return Pipeline.get_pipeline_environment(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.envPipelineUri,
            data=None,
            check_perm=True,
        )


def list_pipeline_environments(context: Context, source: models.DataPipeline, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Pipeline.paginated_pipeline_environments(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.DataPipelineUri,
            data=filter,
            check_perm=None,
        )


def get_pipeline_org(context: Context, source: models.DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env = session.query(models.Environment).get(source.environmentUri)
        org = session.query(models.Organization).get(env.organizationUri)
    return org


def get_clone_url_http(context: Context, source: models.DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env: models.Environment = session.query(models.Environment).get(
            source.environmentUri
        )
        return f'codecommit::{env.region}://{source.repo}'


def cat(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['DataPipelineUri'],
            data=None,
            check_perm=True,
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
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['DataPipelineUri'],
            data=None,
            check_perm=True,
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
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=DataPipelineUri,
            data=None,
            check_perm=True,
        )
        task = models.Task(action='repo.datapipeline.branches', targetUri=DataPipelineUri)
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )
    return response[0]['response']


def get_stack(context, source: models.DataPipeline, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.DataPipelineUri,
        environmentUri=source.environmentUri,
    )


def get_job_runs(context, source: models.DataPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        task = models.Task(targetUri=source.DataPipelineUri, action='glue.job.runs')
        session.add(task)

    response = Worker.process(
        engine=context.engine, task_ids=[task.taskUri], save_response=False
    )[0]
    return response['response']


def get_pipeline_executions(context: Context, source: models.DataPipeline, **kwargs):
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
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=DataPipelineUri,
            permission_name=permissions.CREDENTIALS_PIPELINE,
        )
        pipeline = Pipeline.get_pipeline_by_uri(session, DataPipelineUri)
        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        env_role_arn = env.EnvironmentDefaultIAMRoleArn

        body = _get_creds_from_aws(pipeline, env_role_arn)

    return body


def _get_creds_from_aws(pipeline, env_role_arn):
    aws_account_id = pipeline.AwsAccountId
    aws_session = SessionHelper.remote_session(aws_account_id)
    env_session = SessionHelper.get_session(aws_session, role_arn=env_role_arn)
    c = env_session.get_credentials()
    body = json.dumps(
        {
            'AWS_ACCESS_KEY_ID': c.access_key,
            'AWS_SECRET_ACCESS_KEY': c.secret_key,
            'AWS_SESSION_TOKEN': c.token,
        }
    )
    return body


def list_pipeline_state_machine_executions(
    context: Context, source, DataPipelineUri: str = None, stage: str = None
):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=DataPipelineUri,
            data=None,
            check_perm=True,
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


def start_pipeline(context: Context, source, DataPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=DataPipelineUri,
            permission_name=permissions.START_PIPELINE,
        )

        pipeline = Pipeline.get_pipeline_by_uri(session, DataPipelineUri)

        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        execution_arn = helpers.run_pipeline(state_machine_name=pipeline.name, env=env)

    return execution_arn


def delete_pipeline(
    context: Context, source, DataPipelineUri: str = None, deleteFromAWS: bool = None
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=DataPipelineUri,
            permission_name=permissions.DELETE_PIPELINE,
        )

        pipeline: models.DataPipeline = Pipeline.get_pipeline_by_uri(
            session, DataPipelineUri
        )

        env: models.Environment = Environment.get_environment_by_uri(
            session, pipeline.environmentUri
        )

        Pipeline.delete_pipeline_environments(session, DataPipelineUri)

        KeyValueTag.delete_key_value_tags(session, pipeline.DataPipelineUri, 'pipeline')

        session.delete(pipeline)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=pipeline.DataPipelineUri,
            group=pipeline.SamlGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_repository(
            context=context,
            target_uri=DataPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            repo_name=pipeline.repo,
        )
        if pipeline.devStrategy == "cdk-trunk":
            stack_helper.delete_stack(
                context=context,
                target_uri=DataPipelineUri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region,
                target_type='cdkpipeline',
            )
        else:
            stack_helper.delete_stack(
                context=context,
                target_uri=DataPipelineUri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region,
                target_type='pipeline',
            )

    return True


def delete_pipeline_environment(context: Context, source, envPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        Pipeline.delete_pipeline_environment(
            session=session,
            username=context.username,
            groups=context.groups,
            envPipelineUri=envPipelineUri,
            check_perm=True,
        )
    return True


def update_pipeline_environment(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline_env = Pipeline.update_pipeline_environment(
            session=session,
            username=context.username,
            groups=context.groups,
            data=input,
            uri=input['pipelineUri'],
            check_perm=True,
        )
    return pipeline_env
