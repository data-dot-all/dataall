import logging

from botocore.exceptions import ClientError

from backend.short_async_tasks import Worker
from .sts import SessionHelper
from ... import db
from ...db import models

log = logging.getLogger('aws:glue')

#TODO
@Worker.handler(path='glue.dataset.database.tables')
def list_tables(engine, task: models.Task):
    with engine.scoped_session() as session:
        dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
            session, task.targetUri
        )
        accountid = dataset.AwsAccountId
        region = dataset.region
        tables = Glue.list_glue_database_tables(
            accountid, dataset.GlueDatabaseName, region
        )
        db.api.DatasetTable.sync(session, dataset.datasetUri, glue_tables=tables)
        return tables


@Worker.handler(path='glue.dataset.crawler.create')
def create_crawler(engine, task: models.Task):
    with engine.scoped_session() as session:
        dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
            session, task.targetUri
        )
        location = task.payload.get('location')
        Glue.create_glue_crawler(
            **{
                'crawler_name': f'{dataset.GlueDatabaseName}-{location}'[:52],
                'region': dataset.region,
                'accountid': dataset.AwsAccountId,
                'database': dataset.GlueDatabaseName,
                'location': location or f's3://{dataset.S3BucketName}',
            }
        )


@Worker.handler(path='glue.crawler.start')
def start_crawler(engine, task: models.Task):
    with engine.scoped_session() as session:
        dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
            session, task.targetUri
        )
        location = task.payload.get('location')
        return Glue.start_glue_crawler(
            {
                'crawler_name': dataset.GlueCrawlerName,
                'region': dataset.region,
                'accountid': dataset.AwsAccountId,
                'database': dataset.GlueDatabaseName,
                'location': location,
            }
        )


@Worker.handler('glue.table.update_column')
def update_table_columns(engine, task: models.Task):
    with engine.scoped_session() as session:
        column: models.DatasetTableColumn = session.query(
            models.DatasetTableColumn
        ).get(task.targetUri)
        table: models.DatasetTable = session.query(models.DatasetTable).get(
            column.tableUri
        )
        try:
            aws_session = SessionHelper.remote_session(table.AWSAccountId)

            Glue.grant_pivot_role_all_table_permissions(aws_session, table)

            glue_client = aws_session.client('glue', region_name=table.region)

            original_table = glue_client.get_table(
                CatalogId=table.AWSAccountId,
                DatabaseName=table.GlueDatabaseName,
                Name=table.name,
            )
            updated_table = {
                k: v
                for k, v in original_table['Table'].items()
                if k
                not in [
                    'CatalogId',
                    'DatabaseName',
                    'CreateTime',
                    'UpdateTime',
                    'CreatedBy',
                    'IsRegisteredWithLakeFormation',
                ]
            }
            all_columns = updated_table.get('StorageDescriptor', {}).get(
                'Columns', []
            ) + updated_table.get('PartitionKeys', [])
            for col in all_columns:
                if col['Name'] == column.name:
                    col['Comment'] = column.description
                    log.info(
                        f'Found column {column.name} adding description {column.description}'
                    )
                    response = glue_client.update_table(
                        DatabaseName=table.GlueDatabaseName,
                        TableInput=updated_table,
                    )
                    log.info(
                        f'Column {column.name} updated successfully: {response}'
                    )
            return True

        except ClientError as e:
            log.error(
                f'Failed to update table column {column.name} description: {e}'
            )
            raise e


@Worker.handler('glue.table.columns')
def get_table_columns(engine, task: models.Task):
    with engine.scoped_session() as session:
        dataset_table: models.DatasetTable = session.query(models.DatasetTable).get(
            task.targetUri
        )
        aws = SessionHelper.remote_session(dataset_table.AWSAccountId)
        glue_client = aws.client('glue', region_name=dataset_table.region)
        glue_table = {}
        try:
            glue_table = glue_client.get_table(
                CatalogId=dataset_table.AWSAccountId,
                DatabaseName=dataset_table.GlueDatabaseName,
                Name=dataset_table.name,
            )
        except glue_client.exceptions.ClientError as e:
            log.error(
                f'Failed to get table aws://{dataset_table.AWSAccountId}'
                f'//{dataset_table.GlueDatabaseName}'
                f'//{dataset_table.name} due to: '
                f'{e}'
            )
        db.api.DatasetTable.sync_table_columns(
            session, dataset_table, glue_table['Table']
        )
    return True


@Worker.handler(path='glue.job.runs')
def get_job_runs(engine, task: models.Task):
    with engine.scoped_session() as session:
        Data_pipeline: models.DataPipeline = session.query(models.DataPipeline).get(
            task.targetUri
        )
        aws = SessionHelper.remote_session(Data_pipeline.AwsAccountId)
        glue_client = aws.client('glue', region_name=Data_pipeline.region)
        try:
            response = glue_client.get_job_runs(JobName=Data_pipeline.name)
            print(response)
        except ClientError as e:
            log.warning(f'Could not retrieve pipeline runs , {str(e)}')
            return []
        return response['JobRuns']


@Worker.handler('glue.job.start_profiling_run')
def start_profiling_run(engine, task: models.Task):
    with engine.scoped_session() as session:
        profiling: models.DatasetProfilingRun = (
            db.api.DatasetProfilingRun.get_profiling_run(
                session, profilingRunUri=task.targetUri
            )
        )
        dataset: models.Dataset = session.query(models.Dataset).get(
            profiling.datasetUri
        )
        run = Glue.run_job(
            **{
                'accountid': dataset.AwsAccountId,
                'name': dataset.GlueProfilingJobName,
                'region': dataset.region,
                'arguments': (
                    {'--table': profiling.GlueTableName}
                    if profiling.GlueTableName
                    else {}
                ),
            }
        )
        db.api.DatasetProfilingRun.update_run(
            session,
            profilingRunUri=profiling.profilingRunUri,
            GlueJobRunId=run['JobRunId'],
        )
        return run


@Worker.handler('glue.job.profiling_run_status')
def get_profiling_run(engine, task: models.Task):
    with engine.scoped_session() as session:
        profiling: models.DatasetProfilingRun = (
            db.api.DatasetProfilingRun.get_profiling_run(
                session, profilingRunUri=task.targetUri
            )
        )
        dataset: models.Dataset = session.query(models.Dataset).get(
            profiling.datasetUri
        )
        glue_run = Glue.get_job_run(
            **{
                'accountid': dataset.AwsAccountId,
                'name': dataset.GlueProfilingJobName,
                'region': dataset.region,
                'run_id': profiling.GlueJobRunId,
            }
        )
        profiling.status = glue_run['JobRun']['JobRunState']
        session.commit()
        return profiling.status
