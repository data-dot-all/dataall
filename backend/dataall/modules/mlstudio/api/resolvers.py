import logging
#TODO: fix imports
from dataall.api.context import Context
from dataall.db import exceptions
from dataall.api.Objects.Stack import stack_helper
from dataall.modules.mlstudio.api.enums import SagemakerStudioRole
from dataall.modules.mlstudio.services.services import SagemakerStudioService, SagemakerStudioCreationRequest
from dataall.modules.mlstudio.db.models import SageMakerStudioUserProfile


from .... import db
from ....aws.handlers.sagemaker_studio import (
    SagemakerStudio,
)
from ....db import exceptions, permissions, models
from ....db.api import ResourcePolicy, Stack

log = logging.getLogger(__name__)

class RequestValidator:
    """Aggregates all validation logic for operating with mlstudio"""
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

        required(data, "environmentUri")
        required(data, "SamlAdminGroupName")

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)

def create_sagemaker_studio_user(context: Context, source, input: dict = None):
    """Creates an ML Studio user. Deploys the ML Studio stack into AWS"""
    RequestValidator.validate_creation_request(input)
    request = SagemakerStudioCreationRequest.from_dict(input)
    return SagemakerStudioService.create_sagemaker_studio_user(
        uri=input["environmentUri"],
        admin_group=input["SamlAdminGroupName"],
        request=request
    )

def list_sagemaker_studio_users(context, source, filter: dict = None):
    """
    Lists all SageMaker Studio users using the given filter.
    If the filter is not provided, all users are returned.
    """
    if not filter:
        filter = {}
    return SagemakerStudioService.list_sagemaker_studio_users(filter=filter)


def get_sagemaker_studio_user(
    context, source, sagemakerStudioUserProfileUri: str = None
) -> models.SagemakerStudioUserProfile:
    return SagemakerStudioService.get_sagemaker_studio_user(uri=sagemakerStudioUserProfileUri)


def get_sagemaker_studio_user_profile_presigned_url(
    context,
    source: models.SagemakerStudioUserProfile,
    sagemakerStudioUserProfileUri: str,
):
    # TODO: move logic to service
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=sagemakerStudioUserProfileUri,
            permission_name=permissions.SGMSTUDIO_NOTEBOOK_URL,
            groups=context.groups,
            username=context.username,
        )
        sm_user_profile = db.api.SgmStudioNotebook.get_notebook_by_uri(
            session, sagemakerStudioUserProfileUri
        )

        url = SagemakerStudio.presigned_url(
            AwsAccountId=sm_user_profile.AWSAccountId,
            region=sm_user_profile.region,
            sagemakerStudioDomainID=sm_user_profile.sagemakerStudioDomainID,
            sagemakerStudioUserProfileNameSlugify=sm_user_profile.sagemakerStudioUserProfileNameSlugify,
        )
        return url


def get_user_profile_applications(context, source: models.SagemakerStudioUserProfile):
    # TODO: move logic to service
    if not source:
        return None
    with context.engine.scoped_session() as session:
        sm_user_profile = get_sagemaker_studio_user_profile(
            context,
            source=source,
            sagemakerStudioUserProfileUri=source.sagemakerStudioUserProfileUri,
        )

        user_profiles_applications = SagemakerStudio.get_user_profile_applications(
            AwsAccountId=sm_user_profile.AWSAccountId,
            region=sm_user_profile.region,
            sagemakerStudioDomainID=sm_user_profile.sagemakerStudioDomainID,
            sagemakerStudioUserProfileNameSlugify=sm_user_profile.sagemakerStudioUserProfileNameSlugify,
        )

        return user_profiles_applications


def delete_sagemaker_studio_user_profile(
    context,
    source: models.SagemakerStudioUserProfile,
    sagemakerStudioUserProfileUri: str = None,
    deleteFromAWS: bool = None,
):
    # TODO: move logic to service
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=sagemakerStudioUserProfileUri,
            permission_name=permissions.DELETE_SGMSTUDIO_NOTEBOOK,
            groups=context.groups,
            username=context.username,
        )
        sm_user_profile = db.api.SgmStudioNotebook.get_notebook_by_uri(
            session, sagemakerStudioUserProfileUri
        )
        env: models.Environment = db.api.Environment.get_environment_by_uri(
            session, sm_user_profile.environmentUri
        )

        session.delete(sm_user_profile)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=sm_user_profile.sagemakerStudioUserProfileUri,
            group=sm_user_profile.SamlAdminGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            target_uri=sagemakerStudioUserProfileUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region
        )

    return True

def resolve_user_role(context: Context, source: models.SagemakerStudioUserProfile):
    # TODO: move logic to service
    if source.owner == context.username:
        return SagemakerStudioRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return SagemakerStudioRole.Admin.value
    return SagemakerStudioRole.NoPermission.value


def resolve_mlstudio_status(context, source: models.SagemakerStudioUserProfile, **kwargs):
    # TODO: move logic to service
    if not source:
        return None
    try:
        user_profile_status = SagemakerStudio.get_user_profile_status(
            AwsAccountId=source.AWSAccountId,
            region=source.region,
            sagemakerStudioDomainID=source.sagemakerStudioDomainID,
            sagemakerStudioUserProfileNameSlugify=source.sagemakerStudioUserProfileNameSlugify,
        )
        with context.engine.scoped_session() as session:
            sm_user_profile = session.query(models.SagemakerStudioUserProfile).get(
                source.sagemakerStudioUserProfileUri
            )
            sm_user_profile.sagemakerStudioUserProfileStatus = user_profile_status
        return user_profile_status
    except Exception:
        return 'NOT FOUND'

def resolve_mlstudio_stack(
    context: Context, source: models.SagemakerStudioUserProfile, **kwargs
):
    # TODO: move logic to service
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.sagemakerStudioUserProfileUri,
        environmentUri=source.environmentUri,
    )

