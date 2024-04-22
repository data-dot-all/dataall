import logging

from dataall.base.aws.sts import SessionHelper
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SagemakerClient:
    """
    A Sagemaker notebooks proxy client that is used to send requests to AWS
    """

    def __init__(self, notebook: SagemakerNotebook):
        session = SessionHelper.remote_session(notebook.AWSAccountId, notebook.region)
        self._client = session.client('sagemaker', region_name=notebook.region)
        self._instance_name = notebook.NotebookInstanceName

    def get_notebook_instance_status(self) -> str:
        """Remote call to AWS to check the notebook's status"""
        try:
            response = self._client.describe_notebook_instance(NotebookInstanceName=self._instance_name)
            return response.get('NotebookInstanceStatus', 'NOT FOUND')
        except ClientError as e:
            logger.error(f'Could not retrieve instance {self._instance_name} status due to: {e} ')
            return 'NOT FOUND'

    def presigned_url(self):
        """Creates a presigned url for a notebook instance by sending request to AWS"""
        try:
            response = self._client.create_presigned_notebook_instance_url(NotebookInstanceName=self._instance_name)
            return response['AuthorizedUrl']
        except ClientError as e:
            raise e

    def start_instance(self):
        """Starts the notebooks instance by sending a request to AWS"""
        try:
            status = self.get_notebook_instance_status()
            self._client.start_notebook_instance(NotebookInstanceName=self._instance_name)
            return status
        except ClientError as e:
            return e

    def stop_instance(self) -> None:
        """Stops the notebooks instance by sending a request to AWS"""
        try:
            self._client.stop_notebook_instance(NotebookInstanceName=self._instance_name)
        except ClientError as e:
            raise e


def client(notebook: SagemakerNotebook) -> SagemakerClient:
    """Factory method to retrieve the client to send request to AWS"""
    return SagemakerClient(notebook)
