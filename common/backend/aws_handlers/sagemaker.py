import logging

from backend.aws_handlers.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Sagemaker:
    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('sagemaker', region_name=region)

    @staticmethod
    def get_notebook_instance_status(AwsAccountId, region, NotebookInstanceName):
        try:
            client = Sagemaker.client(AwsAccountId, region)
            response = client.describe_notebook_instance(
                NotebookInstanceName=NotebookInstanceName
            )
            return response.get('NotebookInstanceStatus', 'NOT FOUND')
        except ClientError as e:
            logger.error(
                f'Could not retrieve instance {NotebookInstanceName} status due to: {e} '
            )
            return 'NOT FOUND'

    @staticmethod
    def presigned_url(AwsAccountId, region, NotebookInstanceName):
        try:
            client = Sagemaker.client(AwsAccountId, region)
            response = client.create_presigned_notebook_instance_url(
                NotebookInstanceName=NotebookInstanceName
            )
            return response['AuthorizedUrl']
        except ClientError as e:
            raise e

    @staticmethod
    def presigned_url_jupyterlab(AwsAccountId, region, NotebookInstanceName):
        try:
            client = Sagemaker.client(AwsAccountId, region)
            response = client.create_presigned_notebook_instance_url(
                NotebookInstanceName=NotebookInstanceName
            )
            url_parts = response['AuthorizedUrl'].split('?authToken')
            url = url_parts[0] + '/lab' + '?authToken' + url_parts[1]
            return url
        except ClientError as e:
            raise e

    @staticmethod
    def start_instance(AwsAccountId, region, NotebookInstanceName):
        try:
            client = Sagemaker.client(AwsAccountId, region)
            status = Sagemaker.get_notebook_instance_status(
                AwsAccountId, region, NotebookInstanceName
            )
            client.start_notebook_instance(NotebookInstanceName=NotebookInstanceName)
            return status
        except ClientError as e:
            return e

    @staticmethod
    def stop_instance(AwsAccountId, region, NotebookInstanceName):
        try:
            client = Sagemaker.client(AwsAccountId, region)
            client.stop_notebook_instance(NotebookInstanceName=NotebookInstanceName)
        except ClientError as e:
            raise e

    @staticmethod
    def get_security_groups(AwsAccountId, region):
        try:
            session = SessionHelper.remote_session(AwsAccountId)
            client = session.client('ec2', region_name=region)
            response = client.describe_security_groups()
            sgnames = [SG['GroupName'] for SG in response['SecurityGroups']]
            sgindex = [
                i for i, s in enumerate(sgnames) if 'DefaultLinuxSecurityGroup' in s
            ]
            SecurityGroupIds = [response['SecurityGroups'][sgindex[0]]['GroupId']]
            return SecurityGroupIds
        except ClientError as e:
            raise e
