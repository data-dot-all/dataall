import logging

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.modules.omics.db.models import OmicsRun
from dataall.modules.omics.db.omics_repository import OmicsRepository
from botocore.exceptions import ClientError
from dataall.core.environment.services.environment_service import EnvironmentService

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
    def run_omics_workflow(omics_run: OmicsRun, session):
        workflow = OmicsRepository(session).get_workflow(id=omics_run.workflowId)
        group = EnvironmentService.get_environment_group(session, omics_run.SamlAdminGroupName, omics_run.environmentUri)
        print("********",omics_run)
        print(workflow)
        print(group)
        print("******* AccountId: ",omics_run.AwsAccountId,"****** Region: ",omics_run.region)
        client = OmicsClient.client(awsAccountId=omics_run.AwsAccountId, region=omics_run.region)
        try:
            # response = client.start_run(workflowId=omics_run.workflowId, workflowType='READY2RUN', roleArn=group.environmentIAMRoleArn, parameters=omics_run.parameterTemplate )
            response = client.start_run(workflowId=omics_run.workflowId, workflowType='READY2RUN', roleArn='arn:aws:iam::856197974211:role/service-role/OmicsWorkflow-20231010141883',
                                        parameters=omics_run.parameterTemplate, outputUri='s3://kiranenv-env-856197974211-f69y6d4k/omics_run_output/' )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR RUNNING OMICS WORKFLOW'           
        

    
    @staticmethod
    def list_workflows(awsAccountId, region, type) -> list:
        try:
            found_workflows = []
            client = OmicsClient.client(awsAccountId=awsAccountId, region=region)
            paginator = client.get_paginator('list_workflows')
            response_pages = paginator.paginate(
                type=type,
                PaginationConfig={
                    'MaxItems': 1000,
                    'PageSize': 100,
                }
            )
            for page in response_pages:
                found_workflows.extend(page['items'])
            logger.info(f"{type} workflows = {found_workflows}")
            return found_workflows
        except ClientError as e:
            logger.error(
                f'Could not retrieve {type} Omics Workflows status due to: {e} '
            )
            return 'ERROR LISTING WORKFLOWS'
