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
from dataall.modules.mlstudio.aws.sagemaker_studio_client import sm_studio_client
from dataall.modules.mlstudio.db.repositories import SageMakerStudioRepository
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.utils.slugify import slugify
from dataall.modules.mlstudio.db.models import SagemakerStudioUserProfile
from dataall.modules.mlstudio.services.permissions import MANAGE_SGMSTUDIO_NOTEBOOKS, CREATE_SGMSTUDIO_NOTEBOOK, SGMSTUDIO_NOTEBOOK_ALL
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
    @has_tenant_permission(MANAGE_SGMSTUDIO_NOTEBOOKS)
    @has_resource_permission(CREATE_SGMSTUDIO_NOTEBOOK)
    @has_group_permission(CREATE_SGMSTUDIO_NOTEBOOK)
    #TODO: question, why the * here?
    def create_sagemaker_studio_user_profile(*, uri: str, admin_group: str, request:SagemakerStudioCreationRequest):
        """
        Creates an ML Studio user
        Throws an exception if ML Studio is not enabled for the environment
        """
        with _session() as session:
            env = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "notebooksEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_SGMSTUDIO_NOTEBOOK,
                    message=f'ML Studio feature is disabled for the environment {env.label}',
                )
            #TODO: check with v1.5 how the checking affects this method
            response = sm_studio_client(environment=env).get_sagemaker_studio_domain()
            existing_domain = response.get('DomainId', False)

            if not existing_domain:
                raise exceptions.AWSResourceNotAvailable(
                    action='Sagemaker Studio domain',
                    message='Add a VPC to your environment and update the environment stack '
                            'or create a Sagemaker studio domain on your AWS account.',
                )

            sm_user = SagemakerStudioUserProfile(
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
            SageMakerStudioRepository(session).save_sm_studiouser(sm_user)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=SGMSTUDIO_NOTEBOOK_ALL,
                resource_uri=sm_user.sagemakerStudioUserProfileUri,
                resource_type=models.SagemakerStudioUserProfile.__name__,
            )

            if env.SamlGroupName != sm_user.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=SGMSTUDIO_NOTEBOOK_ALL,
                    resource_uri=sm_user.sagemakerStudioUserProfileUri,
                    resource_type=models.SagemakerStudioUserProfile.__name__,
                )


            Stack.create_stack(
                session=session,
                environment_uri=sm_user.environmentUri,
                target_type='sagemakerstudiouserprofile',
                target_uri=sm_user.sagemakerStudioUserProfileUri,
                target_label=sm_user.label,
            )

        stack_helper.deploy_stack(targetUri=sm_user.sagemakerStudioUserProfileUri)

        return sm_user

