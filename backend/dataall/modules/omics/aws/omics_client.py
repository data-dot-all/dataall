import logging
import json

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.modules.omics.db.omics_models import OmicsRun
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
        session = SessionHelper.remote_session(awsAccountId)
        return session.client('omics', region_name=region)

    @staticmethod
    def get_omics_workflow(workflowUri: str, session):
        workflow = OmicsRepository(session).get_workflow(workflowUri=workflowUri)
        environment = EnvironmentRepository.get_environment_by_uri(session=session, uri=workflow.environmentUri)
        client = OmicsClient.client(awsAccountId=environment.AwsAccountId, region=environment.region)
        try:
            response = client.get_workflow(
                id=workflow.id,
                type='READY2RUN'
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve Ready2Run Omics Workflows status due to: {e} '
            )
            raise e

    @staticmethod
    def get_omics_run(session, runUri: str):
        omics_db = OmicsRepository(session)
        omics_run = omics_db.get_omics_run(runUri=runUri)
        workflow = omics_db.get_workflow(workflowUri=omics_run.workflowUri)
        environment = EnvironmentRepository.get_environment_by_uri(session=session, uri=workflow.environmentUri)
        client = OmicsClient.client(awsAccountId=environment.AwsAccountId, region=environment.region)
        try:
            response = client.get_run(id=omics_run.runUri)
            # TODO: remove prints
            print(response)
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR GETTING WORKFLOW RUN'

    @staticmethod
    def run_omics_workflow(omics_run: OmicsRun, session):
        group = EnvironmentService.get_environment_group(session, omics_run.SamlAdminGroupName, omics_run.environmentUri)
        workflow = OmicsRepository(session=session).get_workflow(workflowUri=omics_run.workflowUri)
        client = OmicsClient.client(awsAccountId=omics_run.AwsAccountId, region=omics_run.region)
        try:
            response = client.start_run(
                workflowId=workflow.id,
                workflowType=workflow.type,
                roleArn=group.environmentIAMRoleArn,
                parameters=json.loads(omics_run.parameterTemplate),
                outputUri=omics_run.outputUri
                tags={
                   'Team': f'{omics_run.SamlAdminGroupName}'
                }
            )
            return response
        except ClientError as e:
            # TODO: Check if we need to raise an error!
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


def client() -> OmicsClient:
    return OmicsClient()
