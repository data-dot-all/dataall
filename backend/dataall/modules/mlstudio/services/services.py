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
from dataall.modules.mlstudio.aws.sagemaker_studio_client import client
from dataall.modules.mlstudio.db.repositories import NotebookRepository
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.utils.slugify import slugify
from dataall.modules.mlstudio.db.models import SagemakerStudioUserProfile
from dataall.modules.mlstudio.services import permissions
from dataall.modules.mlstudio.services.permissions import MANAGE_SGMSTUDIO_NOTEBOOKS, CREATE_SGMSTUDIO_NOTEBOOK
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class SagemakerStudioCreationRequest:
    """A request dataclass for ml studio user profile creation. Adds default values for missed parameters"""
    label: str
    VpcId: str
    SubnetId: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = "No description provided"
    VolumeSizeInGB: int = 32
    InstanceType: str = "ml.t3.medium"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{
            k: v for k, v in env.items()
            if k in fields
        })

class SagemakerStudioService:
    """
    Encapsulate the logic of interactions with sagemaker ml studio.
    """
    @staticmethod
    @has_tenant_permission(MANAGE_SGMSTUDIO_NOTEBOOKS)
    @has_resource_permission(CREATE_SGMSTUDIO_NOTEBOOK)
    @has_group_permission(CREATE_SGMSTUDIO_NOTEBOOK)
    def create_sagemaker_studio_user_profile(context: Context, source, input: dict = None):
        """Creates an ML Studio user. Deploys the ML Studio stack into AWS"""
        #TODO modify!!
        RequestValidator.validate_creation_request(input)
        with context.engine.scoped_session() as session:
            if not input.get('environmentUri'):
                raise exceptions.RequiredParameter('environmentUri')
            if not input.get('label'):
                raise exceptions.RequiredParameter('name')

            environment_uri = input.get('environmentUri')

            ResourcePolicy.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=environment_uri,
                permission_name=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
            )

            env: models.Environment = db.api.Environment.get_environment_by_uri(
                session, environment_uri
            )

            if not env.mlStudiosEnabled:
                raise exceptions.UnauthorizedOperation(
                    action=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
                    message=f'ML Studio feature is disabled for the environment {env.label}',
                )

            existing_domain = SagemakerStudio.get_sagemaker_studio_domain(
                env.AwsAccountId, env.region
            )
            input['domain_id'] = existing_domain.get('DomainId', False)

            if not input['domain_id']:
                raise exceptions.AWSResourceNotAvailable(
                    action='Sagemaker Studio domain',
                    message='Add a VPC to your environment and update the environment stack '
                            'or create a Sagemaker studio domain on your AWS account.',
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
                target_type='sagemakerstudiouserprofile',
                target_uri=sm_user_profile.sagemakerStudioUserProfileUri,
                target_label=sm_user_profile.label,
            )

        stack_helper.deploy_stack(targetUri=sm_user_profile.sagemakerStudioUserProfileUri)

        return sm_user_profile

