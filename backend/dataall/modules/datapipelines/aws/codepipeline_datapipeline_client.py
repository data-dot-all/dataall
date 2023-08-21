import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger('aws:codepipeline')


class CodepipelineDatapipelineClient:
    def __init__(self, aws_account_id, region) -> None:
        self._aws_account_id = aws_account_id
        self._region = region
        self._session = SessionHelper.remote_session(aws_account_id)
        self._client = self._session.client('codepipeline', region_name=region)

    def get_pipeline_execution_summaries(self, codepipeline_name):
        executions = []
        try:
            response = self._client.list_pipeline_executions(
                pipelineName=codepipeline_name
            )
            executions = response['pipelineExecutionSummaries']
        except ClientError as e:
            log.warning(
                f'Could not retrieve pipeline executions for {codepipeline_name} aws://{self._aws_account_id}:{self._region}'
            )

        return executions
