import logging

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment

log = logging.getLogger(__name__)


class S3ProfilerClient:
    def __init__(self, env: Environment):
        self._client = SessionHelper.remote_session(env.AwsAccountId, env.region).client('s3', region_name=env.region)
        self._env = env

    def get_profiling_results_from_s3(self, dataset, table, run):
        s3 = self._client
        try:
            key = f'profiling/results/{dataset.datasetUri}/{table.GlueTableName}/{run.GlueJobRunId}/results.json'
            s3.head_object(Bucket=self._env.EnvironmentDefaultBucketName, Key=key)
            response = s3.get_object(Bucket=self._env.EnvironmentDefaultBucketName, Key=key)
            content = str(response['Body'].read().decode('utf-8'))
            return content
        except Exception as e:
            log.error(
                f'Failed to retrieve S3 results for table profiling job '
                f'{table.GlueTableName}//{run.GlueJobRunId} due to {e}'
            )
