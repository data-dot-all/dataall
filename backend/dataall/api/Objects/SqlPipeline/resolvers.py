import json
import logging

from ....aws.handlers import stepfunction as helpers
from ....aws.handlers.service_handlers import Worker
from ....aws.handlers.sts import SessionHelper
from ....db import exceptions, models, permissions
from ....db.api import Environment, KeyValueTag, Pipeline, ResourcePolicy, Stack
from ...constants import DataPipelineRole
from ...context import Context
from ...Objects.Stack import stack_helper

log = logging.getLogger(__name__)


def create_pipeline(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.create_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input["environmentUri"],
            data=input,
            check_perm=True,
        )

        Stack.create_stack(
            session=session,
            environment_uri=pipeline.environmentUri,
            target_type="pipeline",
            target_uri=pipeline.sqlPipelineUri,
            target_label=pipeline.label,
            payload={"account": pipeline.AwsAccountId, "region": pipeline.region},
        )

    stack_helper.deploy_stack(context, pipeline.sqlPipelineUri)

    return pipeline


def update_pipeline(context: Context, source, sqlPipelineUri: str, input: dict = None):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.update_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=sqlPipelineUri,
            data=input,
            check_perm=True,
        )
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


def get_pipeline(context: Context, source, sqlPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=sqlPipelineUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: models.SqlPipeline):
    if not source:
        return None
    if context.username and source.owner == context.username:
        return DataPipelineRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DataPipelineRole.Admin.value
    return DataPipelineRole.NoPermission.value


def get_pipeline_env(context: Context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env = session.query(models.Environment).get(source.environmentUri)
    return env


def get_pipeline_org(context: Context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env = session.query(models.Environment).get(source.environmentUri)
        org = session.query(models.Organization).get(env.organizationUri)
    return org


def get_clone_url_http(context: Context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env: models.Environment = session.query(models.Environment).get(source.environmentUri)
        return f"codecommit::{env.region}://{source.repo}"


def cat(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input["sqlPipelineUri"],
            data=None,
            check_perm=True,
        )
        task = models.Task(
            action="repo.sqlpipeline.cat",
            targetUri=input.get("sqlPipelineUri"),
            payload={
                "absolutePath": input.get("absolutePath"),
                "branch": input.get("branch", "master"),
            },
        )
        session.add(task)

    response = Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return response[0]["response"].decode("ascii")


def ls(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input["sqlPipelineUri"],
            data=None,
            check_perm=True,
        )
        task = models.Task(
            action="repo.sqlpipeline.ls",
            targetUri=input.get("sqlPipelineUri"),
            payload={
                "folderPath": input.get("folderPath", "/"),
                "branch": input.get("branch", "master"),
            },
        )
        session.add(task)

    response = Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return json.dumps(response[0]["response"])


def list_branches(context: Context, source, sqlPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=sqlPipelineUri,
            data=None,
            check_perm=True,
        )
        task = models.Task(action="repo.sqlpipeline.branches", targetUri=sqlPipelineUri)
        session.add(task)

    response = Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return response[0]["response"]


def get_stack(context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.sqlPipelineUri,
        environmentUri=source.environmentUri,
    )


def get_job_runs(context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        task = models.Task(targetUri=source.sqlPipelineUri, action="glue.job.runs")
        session.add(task)

    response = Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)[0]
    return response["response"]


def get_pipeline_executions(context: Context, source: models.SqlPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        task = models.Task(targetUri=source.sqlPipelineUri, action="sqlpipeline.pipeline.executions")
        session.add(task)

    response = Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)[0]
    return response["response"]


def get_creds(context: Context, source, sqlPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=sqlPipelineUri,
            permission_name=permissions.CREDENTIALS_PIPELINE,
        )
        pipeline = Pipeline.get_pipeline_by_uri(session, sqlPipelineUri)
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
            "AWS_ACCESS_KEY_ID": c.access_key,
            "AWS_SECRET_ACCESS_KEY": c.secret_key,
            "AWS_SESSION_TOKEN": c.token,
        }
    )
    return body


def list_pipeline_state_machine_executions(context: Context, source, sqlPipelineUri: str = None, stage: str = None):
    with context.engine.scoped_session() as session:
        pipeline = Pipeline.get_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=sqlPipelineUri,
            data=None,
            check_perm=True,
        )

        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        executions = helpers.list_executions(state_machine_name=pipeline.name, env=env, stage="Prod")

    return {
        "count": len(executions),
        "page": 1,
        "pages": 4,
        "hasNext": False,
        "hasPrevious": False,
        "nodes": executions,
    }


def start_pipeline(context: Context, source, sqlPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=sqlPipelineUri,
            permission_name=permissions.START_PIPELINE,
        )

        pipeline = Pipeline.get_pipeline_by_uri(session, sqlPipelineUri)

        env = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        execution_arn = helpers.run_pipeline(state_machine_name=pipeline.name, env=env)

    return execution_arn


def delete_pipeline(context: Context, source, sqlPipelineUri: str = None, deleteFromAWS: bool = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=sqlPipelineUri,
            permission_name=permissions.DELETE_PIPELINE,
        )

        pipeline: models.SqlPipeline = Pipeline.get_pipeline_by_uri(session, sqlPipelineUri)

        env: models.Environment = Environment.get_environment_by_uri(session, pipeline.environmentUri)

        KeyValueTag.delete_key_value_tags(session, pipeline.sqlPipelineUri, "pipeline")

        session.delete(pipeline)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=pipeline.sqlPipelineUri,
            group=pipeline.SamlGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=sqlPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            target_type="pipeline",
        )

    return True
