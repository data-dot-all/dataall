import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from dataall.modules.s3_datasets.db.dataset_models import DatasetProfilingRun

log = logging.getLogger(__name__)


class GlueDatasetProfilerClient:
    """Controls glue profiling jobs in AWS"""

    def __init__(self, dataset: S3Dataset):
        session = SessionHelper.remote_session(accountid=dataset.AwsAccountId, region=dataset.region)
        self._client = session.client('glue', region_name=dataset.region)
        self._name = dataset.GlueProfilingJobName

    def get_job_status(self, profiling: DatasetProfilingRun):
        """Returns a status of a glue job"""
        run_id = profiling.GlueJobRunId
        try:
            response = self._client.get_job_run(JobName=self._name, RunId=run_id)
            return response['JobRun']['JobRunState']
        except ClientError as e:
            log.error(f'Failed to get job run {run_id} due to: {e}')
            raise e

    def run_job(self, profiling: DatasetProfilingRun):
        """Run glue job. Returns id of the job"""
        args = {'--table': profiling.GlueTableName} if profiling.GlueTableName else {}
        try:
            response = self._client.start_job_run(JobName=self._name, Arguments=args)

            return response['JobRunId']
        except ClientError as e:
            log.error(f'Failed to start profiling job {self._name} due to: {e}')
            raise e
