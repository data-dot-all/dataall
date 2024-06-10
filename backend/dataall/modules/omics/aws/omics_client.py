import logging
import json

from dataall.base.aws.sts import SessionHelper
from dataall.modules.omics.db.omics_models import OmicsRun, OmicsWorkflow
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class OmicsClient:
    """
    An Omics proxy client that is used to send requests to AWS
    """

    def __init__(self, awsAccountId: str, region: str):
        self.awsAccountId = awsAccountId
        self.region = region
        self._client = self.client()

    def client(self):
        session = SessionHelper.remote_session(self.awsAccountId, self.region)
        return session.client('omics', region_name=self.region)

    def get_omics_workflow(self, workflow: OmicsWorkflow):
        try:
            response = self._client.get_workflow(id=workflow.id, type='READY2RUN')
            return response
        except ClientError as e:
            logger.error(f'Could not retrieve Ready2Run Omics Workflows status due to: {e} ')
            raise e

    def get_omics_run(self, uri: str):
        try:
            response = self._client.get_run(id=uri)
            return response
        except ClientError as e:
            logger.error(f'Could not retrieve workflow run status due to: {e} ')
            raise e

    def run_omics_workflow(self, omics_workflow: OmicsWorkflow, omics_run: OmicsRun, role_arn: str):
        try:
            response = self._client.start_run(
                name=omics_run.label,
                workflowId=omics_workflow.id,
                workflowType=omics_workflow.type,
                roleArn=role_arn,
                parameters=json.loads(omics_run.parameterTemplate),
                outputUri=omics_run.outputUri,
                tags={'Team': f'{omics_run.SamlAdminGroupName}', 'dataall': 'True'},
            )
            return response
        except ClientError as e:
            logger.error(f'Could not retrieve workflow run status due to: {e} ')
            raise e

    def list_workflows(self, type: str) -> list:
        try:
            found_workflows = []
            paginator = self._client.get_paginator('list_workflows')
            response_pages = paginator.paginate(
                type=type,
                PaginationConfig={
                    'MaxItems': 1000,
                    'PageSize': 100,
                },
            )
            for page in response_pages:
                found_workflows.extend(page['items'])
            logger.info(f'{type} workflows = {found_workflows}')
            return found_workflows
        except ClientError as e:
            logger.error(f'Could not retrieve {type} Omics Workflows status due to: {e} ')
            raise e

    def delete_omics_run(self, uri: str):
        try:
            response = self._client.delete_run(id=uri)
            return response
        except ClientError as e:
            logger.error(f'Could not delete run due to: {e} ')
            raise e
