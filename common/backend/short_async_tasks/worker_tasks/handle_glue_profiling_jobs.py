import logging

from botocore.exceptions import ClientError

from backend.short_async_tasks import Worker
from backend.utils.aws import Glue
from backend.db import common, module

##TODO Assuming this goes into module Datasets, careful references to datapipeline

log = logging.getLogger('aws:glue')


##TODO this worker I think it is unused
# @Worker.handler(path='glue.job.runs')
# def get_job_runs(engine, task: common.models.Task):
#     with engine.scoped_session() as session:
#         Data_pipeline: module.models.DataPipeline = session.query(module.models.DataPipeline).get(
#             task.targetUri
#         )
#         aws = SessionHelper.remote_session(Data_pipeline.AwsAccountId)
#         glue_client = aws.client('glue', region_name=Data_pipeline.region)
#         try:
#             response = glue_client.get_job_runs(JobName=Data_pipeline.name)
#             print(response)
#         except ClientError as e:
#             log.warning(f'Could not retrieve pipeline runs , {str(e)}')
#             return []
#         return response['JobRuns']


@Worker.handler('glue.job.start_profiling_run')
def start_profiling_run(engine, task: common.models.Task):
    with engine.scoped_session() as session:
        profiling: module.models.DatasetProfilingRun = (
            module.operations.DatasetProfilingRun.get_profiling_run(
                session, profilingRunUri=task.targetUri
            )
        )
        dataset: module.models.Dataset = session.query(module.models.Dataset).get(
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
        module.operations.DatasetProfilingRun.update_run(
            session,
            profilingRunUri=profiling.profilingRunUri,
            GlueJobRunId=run['JobRunId'],
        )
        return run


@Worker.handler('glue.job.profiling_run_status')
def get_profiling_run(engine, task: common.models.Task):
    with engine.scoped_session() as session:
        profiling: module.models.DatasetProfilingRun = (
            module.operations.DatasetProfilingRun.get_profiling_run(
                session, profilingRunUri=task.targetUri
            )
        )
        dataset: module.models.Dataset = session.query(module.models.Dataset).get(
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
