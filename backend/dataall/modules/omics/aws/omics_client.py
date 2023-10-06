import logging

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.modules.omics.db.models import OmicsRun
from dataall.modules.omics.db.omics_repository import OmicsRepository
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OmicsClient:
    """
    An Omics proxy client that is used to send requests to AWS
    """

    @staticmethod
    def client(awsAccountId: str, region: str):
        # session = SessionHelper.remote_session(awsAccountId,'arn:aws:iam::545117064741:role/dataallPivotRole')
        session = SessionHelper.remote_session(awsAccountId)
        return session.client('omics', region_name=region)
        
    @staticmethod
    def get_omics_workflow(id: str, session):
        workflow = OmicsRepository(session).get_workflow(id=id)
        environment = EnvironmentRepository.get_environment_by_uri(session=session, uri=workflow.environmentUri)
        client = OmicsClient.client(awsAccountId=environment.AwsAccountId, region=environment.region)
        try:
            response = client.get_workflow(
                id=id,
                type='READY2RUN'
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve Ready2Run Omics Workflows status due to: {e} '
            )
            return 'ERROR LISTING WORKFLOWS'

    @staticmethod
    def get_workflow_run(id: str, session):
        workflow = OmicsRepository(session).get_workflow(id=id)
        environment = EnvironmentRepository.get_environment_by_uri(session=session, uri=workflow.environmentUri)
        client = OmicsClient.client(awsAccountId=environment.AwsAccountId, region=environment.region)
        try:
            response = client.get_run(id=id
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR GETTING WORKFLOW RUN'    
        

    @staticmethod
    def run_omics_workflow(self, workflowId: str, workflowType: str, roleArn: str, parameters: str, session):
        workflow = OmicsRepository(session).get_workflow(id=id)
        environment = EnvironmentRepository.get_environment_by_uri(session=session, uri=workflow.environmentUri)
        client = OmicsClient.client(awsAccountId=environment.AwsAccountId, region=environment.region)
        try:
            response = client.start_run(workflowId, workflowType, roleArn, parameters
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR RUNNING OMICS WORKFLOW'           
        

    
    @staticmethod
    def list_workflows(awsAccountId, region) -> list:
        try:
            client = OmicsClient.client(awsAccountId=awsAccountId, region=region)
            paginator = client.get_paginator('list_workflows')
            response_pages = paginator.paginate(
                PaginationConfig={
                    'MaxItems': 100,
                    'PageSize': 100,
                }
            )
            found_workflows = []
            for page in response_pages:
                found_workflows.extend(page['items'])
            return found_workflows
        except ClientError as e:
            logger.error(
                f'Could not retrieve Ready2Run Omics Workflows status due to: {e} '
            )
            return 'ERROR LISTING WORKFLOWS'
