import logging
from botocore.exceptions import ClientError

from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.modules.datasets_base.db.models import DatasetProfilingRun, Dataset
from dataall.modules.datasets.db.dataset_profiling_repository import DatasetProfilingRepository

log = logging.getLogger(__name__)


class DatasetProfilingGlueHandler:
    """A handler for dataset profiling"""

    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            profiling: DatasetProfilingRun = (
                DatasetProfilingRepository.get_profiling_run(
                    session, profilingRunUri=task.targetUri
                )
            )
            dataset: Dataset = session.query(Dataset).get(
                profiling.datasetUri
            )
            glue_run = DatasetProfilingGlueHandler.get_job_run(
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

    @staticmethod
    @Worker.handler('glue.job.start_profiling_run')
    def start_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            profiling: DatasetProfilingRun = (
                DatasetProfilingRepository.get_profiling_run(
                    session, profilingRunUri=task.targetUri
                )
            )
            dataset: Dataset = session.query(Dataset).get(
                profiling.datasetUri
            )
            run = DatasetProfilingGlueHandler.run_job(
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
            DatasetProfilingRepository.update_run(
                session,
                profilingRunUri=profiling.profilingRunUri,
                GlueJobRunId=run['JobRunId'],
            )
            return run

    # TODO move to client once dataset is migrated
    @staticmethod
    def get_job_run(**data):
        accountid = data['accountid']
        name = data['name']
        run_id = data['run_id']
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            client = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            response = client.get_job_run(JobName=name, RunId=run_id)
            return response
        except ClientError as e:
            log.error(f'Failed to get job run {run_id} due to: {e}')
            raise e

    @staticmethod
    def run_job(**data):
        accountid = data['accountid']
        name = data['name']
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            client = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            response = client.start_job_run(
                JobName=name, Arguments=data.get('arguments', {})
            )
            return response
        except ClientError as e:
            log.error(f'Failed to start profiling job {name} due to: {e}')
            raise e
