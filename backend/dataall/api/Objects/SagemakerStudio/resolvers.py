import logging

from ..Stack import stack_helper
from .... import db
from ....api.constants import SagemakerStudioRole
from ....api.context import Context
from ....aws.handlers.sagemaker_studio import (
    SagemakerStudio,
)
from ....db import exceptions, permissions, models
from ....db.api import ResourcePolicy, Stack

log = logging.getLogger(__name__)


def create_sagemaker_studio_user_profile(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        if not input.get("environmentUri"):
            raise exceptions.RequiredParameter("environmentUri")
        if not input.get("label"):
            raise exceptions.RequiredParameter("name")

        environment_uri = input.get("environmentUri")

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environment_uri,
            permission_name=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
        )

        env: models.Environment = db.api.Environment.get_environment_by_uri(session, environment_uri)

        if not env.mlStudiosEnabled:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
                message=f"ML Studio feature is disabled for the environment {env.label}",
            )

        existing_domain = SagemakerStudio.get_sagemaker_studio_domain(env.AwsAccountId, env.region)
        input["domain_id"] = existing_domain.get("DomainId", False)

        if not input["domain_id"]:
            raise exceptions.AWSResourceNotAvailable(
                action="Sagemaker Studio domain",
                message="Add a VPC to your environment and update the environment stack "
                "or create a Sagemaker studio domain on your AWS account.",
            )

        sm_user_profile = db.api.SgmStudioNotebook.create_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=env.environmentUri,
            data=input,
            check_perm=True,
        )

        Stack.create_stack(
            session=session,
            environment_uri=sm_user_profile.environmentUri,
            target_type="sagemakerstudiouserprofile",
            target_uri=sm_user_profile.sagemakerStudioUserProfileUri,
            target_label=sm_user_profile.label,
        )

    stack_helper.deploy_stack(context=context, targetUri=sm_user_profile.sagemakerStudioUserProfileUri)

    return sm_user_profile


def list_sm_studio_user_profile(context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.SgmStudioNotebook.paginated_user_notebooks(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def get_sagemaker_studio_user_profile(
    context, source, sagemakerStudioUserProfileUri: str = None
) -> models.SagemakerStudioUserProfile:
    with context.engine.scoped_session() as session:
        return db.api.SgmStudioNotebook.get_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=sagemakerStudioUserProfileUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: models.SagemakerStudioUserProfile):
    if source.owner == context.username:
        return SagemakerStudioRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return SagemakerStudioRole.Admin.value
    return SagemakerStudioRole.NoPermission.value


def resolve_status(context, source: models.SagemakerStudioUserProfile, **kwargs):
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
            sm_user_profile = session.query(models.SagemakerStudioUserProfile).get(source.sagemakerStudioUserProfileUri)
            sm_user_profile.sagemakerStudioUserProfileStatus = user_profile_status
        return user_profile_status
    except Exception:
        return "NOT FOUND"


def get_sagemaker_studio_user_profile_presigned_url(
    context,
    source: models.SagemakerStudioUserProfile,
    sagemakerStudioUserProfileUri: str,
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=sagemakerStudioUserProfileUri,
            permission_name=permissions.SGMSTUDIO_NOTEBOOK_URL,
            groups=context.groups,
            username=context.username,
        )
        sm_user_profile = db.api.SgmStudioNotebook.get_notebook_by_uri(session, sagemakerStudioUserProfileUri)

        url = SagemakerStudio.presigned_url(
            AwsAccountId=sm_user_profile.AWSAccountId,
            region=sm_user_profile.region,
            sagemakerStudioDomainID=sm_user_profile.sagemakerStudioDomainID,
            sagemakerStudioUserProfileNameSlugify=sm_user_profile.sagemakerStudioUserProfileNameSlugify,
        )
        return url


def get_user_profile_applications(context, source: models.SagemakerStudioUserProfile):
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
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=sagemakerStudioUserProfileUri,
            permission_name=permissions.DELETE_SGMSTUDIO_NOTEBOOK,
            groups=context.groups,
            username=context.username,
        )
        sm_user_profile = db.api.SgmStudioNotebook.get_notebook_by_uri(session, sagemakerStudioUserProfileUri)
        env: models.Environment = db.api.Environment.get_environment_by_uri(session, sm_user_profile.environmentUri)

        session.delete(sm_user_profile)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=sm_user_profile.sagemakerStudioUserProfileUri,
            group=sm_user_profile.SamlAdminGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=sagemakerStudioUserProfileUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            target_type="notebook",
        )

    return True


def resolve_environment(context, source, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return session.query(models.Environment).get(source.environmentUri)


def resolve_organization(context, source, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env: models.Environment = session.query(models.Environment).get(source.environmentUri)
        return session.query(models.Organization).get(env.organizationUri)


def resolve_stack(context: Context, source: models.SagemakerStudioUserProfile, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.sagemakerStudioUserProfileUri,
        environmentUri=source.environmentUri,
    )
