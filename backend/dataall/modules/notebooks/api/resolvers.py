from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.notebooks.api.enums import SagemakerNotebookRole
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.modules.notebooks.services.notebook_service import NotebookService, NotebookCreationRequest


def create_notebook(context: Context, source: SagemakerNotebook, input: dict = None):
    """Creates a SageMaker notebook. Deploys the notebooks stack into AWS"""
    RequestValidator.validate_creation_request(input)
    request = NotebookCreationRequest.from_dict(input)
    return NotebookService.create_notebook(
        uri=input['environmentUri'], admin_group=input['SamlAdminGroupName'], request=request
    )


def list_notebooks(context, source, filter: dict = None):
    """
    Lists all SageMaker notebooks using the given filter.
    If the filter is not provided, all notebooks are returned.
    """

    if not filter:
        filter = {}
    return NotebookService.list_user_notebooks(filter)


def get_notebook(context, source, notebookUri: str = None):
    """Retrieve a SageMaker notebook by URI."""
    RequestValidator.required_uri(notebookUri)
    return NotebookService.get_notebook(uri=notebookUri)


def resolve_notebook_status(context, source: SagemakerNotebook, **kwargs):
    """Resolves the status of a notebook."""
    if not source:
        return None
    return NotebookService.get_notebook_status(uri=source.notebookUri)


def start_notebook(context, source: SagemakerNotebook, notebookUri: str = None):
    """Starts a sagemaker notebook instance"""
    RequestValidator.required_uri(notebookUri)
    NotebookService.start_notebook(uri=notebookUri)
    return 'Starting'


def stop_notebook(context, source: SagemakerNotebook, notebookUri: str = None):
    """Stops a notebook instance."""
    RequestValidator.required_uri(notebookUri)
    NotebookService.stop_notebook(uri=notebookUri)
    return 'Stopping'


def get_notebook_presigned_url(context, source: SagemakerNotebook, notebookUri: str = None):
    """Creates and returns a presigned url for a notebook"""
    RequestValidator.required_uri(notebookUri)
    return NotebookService.get_notebook_presigned_url(uri=notebookUri)


def delete_notebook(
    context,
    source: SagemakerNotebook,
    notebookUri: str = None,
    deleteFromAWS: bool = None,
):
    """
    Deletes the SageMaker notebook.
    Deletes the notebooks stack from AWS if deleteFromAWS is True
    """
    RequestValidator.required_uri(notebookUri)
    NotebookService.delete_notebook(uri=notebookUri, delete_from_aws=deleteFromAWS)
    return True


def resolve_user_role(context: Context, source: SagemakerNotebook):
    if not source:
        return None
    if source.owner == context.username:
        return SagemakerNotebookRole.CREATOR.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return SagemakerNotebookRole.ADMIN.value
    return SagemakerNotebookRole.NO_PERMISSION.value


def resolve_notebook_stack(context: Context, source: SagemakerNotebook, **kwargs):
    if not source:
        return None
    return StackService.resolve_parent_obj_stack(
        targetUri=source.notebookUri,
        targetType='notebook',
        environmentUri=source.environmentUri,
    )


class RequestValidator:
    """Aggregates all validation logic for operating with notebooks"""

    @staticmethod
    def required_uri(uri):
        if not uri:
            raise exceptions.RequiredParameter('URI')

    @staticmethod
    def validate_creation_request(data):
        required = RequestValidator._required
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

        required(data, 'environmentUri')
        required(data, 'SamlAdminGroupName')

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)
