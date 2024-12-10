import logging

from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.mlstudio.api.enums import SagemakerStudioRole
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser
from dataall.modules.mlstudio.services.mlstudio_service import SagemakerStudioService, SagemakerStudioCreationRequest

log = logging.getLogger(__name__)


class RequestValidator:
    """Aggregates all validation logic for operating with mlstudio"""

    @staticmethod
    def required_uri(uri):
        if not uri:
            raise exceptions.RequiredParameter('URI')

    @staticmethod
    def validate_user_creation_request(data):
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


def create_sagemaker_studio_user(context: Context, source, input: dict = None):
    """Creates a SageMaker Studio user. Deploys the SageMaker Studio user stack into AWS"""
    RequestValidator.validate_user_creation_request(input)
    request = SagemakerStudioCreationRequest.from_dict(input)
    return SagemakerStudioService.create_sagemaker_studio_user(
        uri=input['environmentUri'], admin_group=input['SamlAdminGroupName'], request=request
    )


def list_sagemaker_studio_users(context, source, filter: dict = None):
    """
    Lists all SageMaker Studio users using the given filter.
    If the filter is not provided, all users are returned.
    """
    if not filter:
        filter = {}
    return SagemakerStudioService.list_sagemaker_studio_users(filter=filter)


def get_sagemaker_studio_user(context, source, sagemakerStudioUserUri: str = None) -> SagemakerStudioUser:
    """Retrieve a SageMaker Studio user by URI."""
    RequestValidator.required_uri(sagemakerStudioUserUri)
    return SagemakerStudioService.get_sagemaker_studio_user(uri=sagemakerStudioUserUri)


def get_sagemaker_studio_user_presigned_url(
    context,
    source: SagemakerStudioUser,
    sagemakerStudioUserUri: str,
) -> str:
    """Creates and returns a presigned url for a SageMaker Studio user"""
    RequestValidator.required_uri(sagemakerStudioUserUri)
    return SagemakerStudioService.get_sagemaker_studio_user_presigned_url(uri=sagemakerStudioUserUri)


def delete_sagemaker_studio_user(
    context,
    source: SagemakerStudioUser,
    sagemakerStudioUserUri: str = None,
    deleteFromAWS: bool = None,
):
    """
    Deletes the SageMaker Studio user.
    Deletes the SageMaker Studio user stack from AWS if deleteFromAWS is True
    """
    RequestValidator.required_uri(sagemakerStudioUserUri)
    return SagemakerStudioService.delete_sagemaker_studio_user(
        uri=sagemakerStudioUserUri, delete_from_aws=deleteFromAWS
    )


def get_environment_sagemaker_studio_domain(context, source, environmentUri: str = None):
    RequestValidator.required_uri(environmentUri)
    return SagemakerStudioService.get_environment_sagemaker_studio_domain(environment_uri=environmentUri)


def resolve_user_role(context: Context, source: SagemakerStudioUser):
    """
    Resolves the role of the current user in reference with the SageMaker Studio User
    """
    if not source:
        return None
    if source.owner == context.username:
        return SagemakerStudioRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return SagemakerStudioRole.Admin.value
    return SagemakerStudioRole.NoPermission.value


def resolve_sagemaker_studio_user_status(context, source: SagemakerStudioUser, **kwargs):
    """
    Resolves the status of the SageMaker Studio User
    """
    if not source:
        return None
    return SagemakerStudioService.get_sagemaker_studio_user_status(uri=source.sagemakerStudioUserUri)


def resolve_sagemaker_studio_user_stack(context: Context, source: SagemakerStudioUser, **kwargs):
    """
    Resolves the status of the CloudFormation stack of the SageMaker Studio User
    """
    if not source:
        return None
    return StackService.resolve_parent_obj_stack(
        targetUri=source.sagemakerStudioUserUri,
        targetType='mlstudio',
        environmentUri=source.environmentUri,
    )


def resolve_sagemaker_studio_user_applications(context, source: SagemakerStudioUser):
    """
    Resolves the applications created with this SageMaker Studio User
    """
    if not source:
        return None
    return SagemakerStudioService.get_sagemaker_studio_user_applications(uri=source.sagemakerStudioUserUri)
