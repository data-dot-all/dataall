import logging

from botocore.exceptions import ClientError

from dataall.aws.handlers.sts import SessionHelper

log = logging.getLogger('aws:glue')


class GlueDatapipelineClient:
    def __init__(self, aws_account_id, region) -> None:
        self._session = SessionHelper.remote_session(aws_account_id)
        self._client = self._session.client('glue', region_name=region)

    def get_job_runs(self, datapipeline_job_name):
        try:
            response = self._client.get_job_runs(JobName=datapipeline_job_name)
        except ClientError as e:
            log.warning(f'Could not retrieve pipeline runs , {str(e)}')
            return []
        return response['JobRuns']
