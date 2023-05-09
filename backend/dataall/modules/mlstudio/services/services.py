"""
A service layer for ml studio
Central part for working with ml studio
"""
import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.api.Objects.Stack import stack_helper
from dataall.core.context import get_context as context
from dataall.core.environment.db.repositories import EnvironmentParameterRepository
from dataall.db.api import (
    ResourcePolicy,
    Environment, KeyValueTag, Stack,
)
from dataall.db import models, exceptions
from dataall.modules.mlstudio.aws.sagemaker_studio_client import sagemaker_studio_client
from dataall.modules.mlstudio.db.repositories import SageMakerStudioRepository

from dataall.utils.slugify import slugify
from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from dataall.modules.mlstudio.services.permissions import (
    MANAGE_SGMSTUDIO_USERS,
    CREATE_SGMSTUDIO_USER,
    SGMSTUDIO_USER_ALL,
    GET_SGMSTUDIO_USER,
)
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class SagemakerStudioCreationRequest:
    """A request dataclass for ml studio user profile creation. Adds default values for missed parameters"""
    label: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = "No description provided"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{
            k: v for k, v in env.items()
            if k in fields
        })

def _session():
    return context().db_engine.scoped_session()

class SagemakerStudioService:
    """
    Encapsulate the logic of interactions with sagemaker ml studio.
    """
    @staticmethod
    @has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    @has_resource_permission(CREATE_SGMSTUDIO_USER)
    @has_group_permission(CREATE_SGMSTUDIO_USER)
    #TODO: question, why the * here?
    def create_sagemaker_studio_user(*, uri: str, admin_group: str, request:SagemakerStudioCreationRequest):
        """
        Creates an ML Studio user
        Throws an exception if ML Studio is not enabled for the environment
        """
        with _session() as session:
            env = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "mlstudioEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_SGMSTUDIO_USER,
                    message=f'ML Studio feature is disabled for the environment {env.label}',
                )
            #TODO: check with v1.5 how the checking affects this method
            response = sagemaker_studio_client(environment=env).get_sagemaker_studio_domain()
            existing_domain = response.get('DomainId', False)

            if not existing_domain:
                raise exceptions.AWSResourceNotAvailable(
                    action='Sagemaker Studio domain',
                    message='Add a VPC to your environment and update the environment stack '
                            'or create a Sagemaker studio domain on your AWS account.',
                )

            sagemaker_studio_user = SagemakerStudioUser(
                label=request.label,
                environmentUri=env.environmentUri,
                description=request.description,
                sagemakerStudioUserProfileName=slugify(request.label, separator=''),
                sagemakerStudioUserProfileStatus='PENDING',
                sagemakerStudioDomainID=existing_domain,
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                RoleArn=env.EnvironmentDefaultIAMRoleArn,
                owner=context().username,
                SamlAdminGroupName=admin_group,
                tags=request.tags,
            )
            SageMakerStudioRepository(session).save_sm_user(user=sagemaker_studio_user)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=SGMSTUDIO_USER_ALL,
                resource_uri=sagemaker_studio_user.sagemakerStudioUserProfileUri,
                resource_type=models.SagemakerStudioUserProfile.__name__,
            )

            if env.SamlGroupName != sagemaker_studio_user.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=SGMSTUDIO_USER_ALL,
                    resource_uri=sagemaker_studio_user.sagemakerStudioUserProfileUri,
                    resource_type=models.SagemakerStudioUserProfile.__name__,
                )


            Stack.create_stack(
                session=session,
                environment_uri=sagemaker_studio_user.environmentUri,
                target_type='sagemakerstudiouserprofile',
                target_uri=sagemaker_studio_user.sagemakerStudioUserProfileUri,
                target_label=sagemaker_studio_user.label,
            )

        stack_helper.deploy_stack(targetUri=sagemaker_studio_user.sagemakerStudioUserProfileUri)

        return sagemaker_studio_user

    @staticmethod
    def list_sagemaker_studio_users(*, filter) -> dict:
        with _session() as session:
            return SageMakerStudioRepository(session).paginated_sagemaker_studio_users(
                username=context.username,
                groups=context.groups,
                filter=filter,
            )

    @staticmethod
    @has_resource_permission(GET_SGMSTUDIO_USER)
    def get_sagemaker_studio_user(*, uri):
        with _session() as session:
            user = SageMakerStudioRepository(session).find_sagemaker_studio_user(uri=uri)
            if not user:
                raise exceptions.ObjectNotFound('SagemakerStudioUser', uri)
            return user



