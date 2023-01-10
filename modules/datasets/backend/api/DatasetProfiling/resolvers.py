import json
import logging

from backend.api.context import Context
from backend.aws.service_handlers import Worker
from backend.aws.sts import SessionHelper
from ....db import api, permissions, models
from ....db.api import ResourcePolicy

log = logging.getLogger(__name__)


def resolve_dataset(context, source: models.DatasetProfilingRun):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return api.Dataset.get_dataset_by_uri(
            session=session, dataset_uri=source.datasetUri
        )


def start_profiling_run(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=input['datasetUri'],
            permission_name=permissions.PROFILE_DATASET_TABLE,
        )
        dataset = api.Dataset.get_dataset_by_uri(session, input['datasetUri'])

        run = api.DatasetProfilingRun.start_profiling(
            session=session,
            datasetUri=dataset.datasetUri,
            tableUri=input.get('tableUri'),
            GlueTableName=input.get('GlueTableName'),
        )

        task = models.Task(
            targetUri=run.profilingRunUri, action='glue.job.start_profiling_run'
        )
        session.add(task)

    Worker.process(engine=context.engine, task_ids=[task.taskUri])

    return run


def get_profiling_run_status(context: Context, source: models.DatasetProfilingRun):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        task = models.Task(
            targetUri=source.profilingRunUri, action='glue.job.profiling_run_status'
        )
        session.add(task)
    Worker.queue(engine=context.engine, task_ids=[task.taskUri])
    return source.status


def get_profiling_results(context: Context, source: models.DatasetProfilingRun):
    if not source or source.results == {}:
        return None
    else:
        return json.dumps(source.results)


def update_profiling_run_results(context: Context, source, profilingRunUri, results):
    with context.engine.scoped_session() as session:
        run = api.DatasetProfilingRun.update_run(
            session=session, profilingRunUri=profilingRunUri, results=results
        )
        return run


def list_profiling_runs(context: Context, source, datasetUri=None):
    with context.engine.scoped_session() as session:
        return api.DatasetProfilingRun.list_profiling_runs(session, datasetUri)


def get_profiling_run(context: Context, source, profilingRunUri=None):
    with context.engine.scoped_session() as session:
        return api.DatasetProfilingRun.get_profiling_run(
            session=session, profilingRunUri=profilingRunUri
        )


def get_last_table_profiling_run(context: Context, source, tableUri=None):
    with context.engine.scoped_session() as session:
        run: models.DatasetProfilingRun = (
            api.DatasetProfilingRun.get_table_last_profiling_run(
                session=session, tableUri=tableUri
            )
        )

        if run:
            if not run.results:
                table = api.DatasetTable.get_dataset_table_by_uri(session, tableUri)
                dataset = api.Dataset.get_dataset_by_uri(session, table.datasetUri)
                environment = api.Environment.get_environment_by_uri(
                    session, dataset.environmentUri
                )
                content = get_profiling_results_from_s3(
                    environment, dataset, table, run
                )
                if content:
                    results = json.loads(content)
                    run.results = results

            if not run.results:
                run_with_results = (
                    api.DatasetProfilingRun.get_table_last_profiling_run_with_results(
                        session=session, tableUri=tableUri
                    )
                )
                if run_with_results:
                    run = run_with_results

        return run


def get_profiling_results_from_s3(environment, dataset, table, run):
    s3 = SessionHelper.remote_session(environment.AwsAccountId).client(
        's3', region_name=environment.region
    )
    try:
        key = f'profiling/results/{dataset.datasetUri}/{table.GlueTableName}/{run.GlueJobRunId}/results.json'
        s3.head_object(Bucket=environment.EnvironmentDefaultBucketName, Key=key)
        response = s3.get_object(
            Bucket=environment.EnvironmentDefaultBucketName, Key=key
        )
        content = str(response['Body'].read().decode('utf-8'))
        return content
    except Exception as e:
        log.error(
            f'Failed to retrieve S3 results for table profiling job '
            f'{table.GlueTableName}//{run.GlueJobRunId} due to {e}'
        )


def list_table_profiling_runs(context: Context, source, tableUri=None):
    with context.engine.scoped_session() as session:
        return api.DatasetProfilingRun.list_table_profiling_runs(
            session=session, tableUri=tableUri, filter={}
        )
