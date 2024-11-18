"""
A service layer for ml studio
Central part for working with ml studio
"""

import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.base.context import get_context
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.base.db import exceptions
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.mlstudio.aws.sagemaker_studio_client import sagemaker_studio_client, get_sagemaker_studio_domain
from dataall.modules.mlstudio.db.mlstudio_repositories import SageMakerStudioRepository
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser
from dataall.base.aws.ec2_client import EC2
from dataall.base.aws.sts import SessionHelper

from dataall.modules.mlstudio.services.mlstudio_permissions import (
    MANAGE_SGMSTUDIO_USERS,
    CREATE_SGMSTUDIO_USER,
    SGMSTUDIO_USER_ALL,
    GET_SGMSTUDIO_USER,
    SGMSTUDIO_USER_URL,
    DELETE_SGMSTUDIO_USER,
)
from dataall.base.utils import slugify

logger = logging.getLogger(__name__)


@dataclass
class SagemakerStudioCreationRequest:
    """A request dataclass for ml studio user profile creation. Adds default values for missed parameters"""

    label: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = 'No description provided'
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{k: v for k, v in env.items() if k in fields})


def _session():
    return get_context().db_engine.scoped_session()


class SagemakerStudioEnvironmentResource(EnvironmentResource):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return SageMakerStudioRepository.count_resources(session, environment, group_uri)

    @staticmethod
    def create_env(session, environment, **kwargs):
        enabled = EnvironmentService.get_boolean_env_param(session, environment, 'mlStudiosEnabled')
        if enabled:
            SagemakerStudioService.create_sagemaker_studio_domain(session, environment, **kwargs)

    @staticmethod
    def update_env(session, environment, **kwargs):
        current_mlstudio_enabled = EnvironmentService.get_boolean_env_param(session, environment, 'mlStudiosEnabled')
        domain = SageMakerStudioRepository.get_sagemaker_studio_domain_by_env_uri(session, environment.environmentUri)
        previous_mlstudio_enabled = True if domain else False
        if current_mlstudio_enabled != previous_mlstudio_enabled and previous_mlstudio_enabled:
            SageMakerStudioRepository.delete_sagemaker_studio_domain_by_env_uri(
                session=session, env_uri=environment.environmentUri
            )
            return True
        elif current_mlstudio_enabled != previous_mlstudio_enabled and not previous_mlstudio_enabled:
            SagemakerStudioService.create_sagemaker_studio_domain(session, environment, **kwargs)
            return True
        elif current_mlstudio_enabled and domain and domain.vpcType == 'unknown':
            SagemakerStudioService.update_sagemaker_studio_domain(environment, domain, **kwargs)
            return True
        return False

    @staticmethod
    def delete_env(session, environment):
        SageMakerStudioRepository.delete_sagemaker_studio_domain_by_env_uri(
            session=session, env_uri=environment.environmentUri
        )


class SagemakerStudioService:
    """
    Encapsulate the logic of interactions with sagemaker ml studio.
    """

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    @ResourcePolicyService.has_resource_permission(CREATE_SGMSTUDIO_USER)
    @GroupPolicyService.has_group_permission(CREATE_SGMSTUDIO_USER)
    def create_sagemaker_studio_user(*, uri: str, admin_group: str, request: SagemakerStudioCreationRequest):
        """
        Creates an ML Studio user
        Throws an exception if ML Studio is not enabled for the environment
        Throws an exception if a SageMaker domain is not found
        """
        with _session() as session:
            env = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, env, 'mlStudiosEnabled')

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_SGMSTUDIO_USER,
                    message=f'ML Studio feature is disabled for the environment {env.label}',
                )

            domain = SageMakerStudioRepository.get_sagemaker_studio_domain_by_env_uri(
                session, env_uri=env.environmentUri
            )
            response = get_sagemaker_studio_domain(
                AwsAccountId=env.AwsAccountId, region=env.region, domain_name=domain.sagemakerStudioDomainName
            )
            existing_domain = response.get('DomainId', False)

            if not existing_domain:
                raise exceptions.AWSResourceNotAvailable(
                    action='Sagemaker Studio domain',
                    message='Update the environment stack and enable ML Studio Environment Feature',
                )

            sagemaker_studio_user = SagemakerStudioUser(
                label=request.label,
                environmentUri=env.environmentUri,
                description=request.description,
                sagemakerStudioUserName=slugify(request.label, separator=''),
                sagemakerStudioUserStatus='PENDING',
                sagemakerStudioDomainID=existing_domain,
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                RoleArn=env.EnvironmentDefaultIAMRoleArn,
                owner=get_context().username,
                SamlAdminGroupName=admin_group,
                tags=request.tags,
            )
            SageMakerStudioRepository.save_sagemaker_studio_user(session, sagemaker_studio_user)

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=SGMSTUDIO_USER_ALL,
                resource_uri=sagemaker_studio_user.sagemakerStudioUserUri,
                resource_type=SagemakerStudioUser.__name__,
            )

            if env.SamlGroupName != sagemaker_studio_user.SamlAdminGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=SGMSTUDIO_USER_ALL,
                    resource_uri=sagemaker_studio_user.sagemakerStudioUserUri,
                    resource_type=SagemakerStudioUser.__name__,
                )

            StackRepository.create_stack(
                session=session,
                environment_uri=sagemaker_studio_user.environmentUri,
                target_type='mlstudio',
                target_uri=sagemaker_studio_user.sagemakerStudioUserUri,
            )

        StackService.deploy_stack(targetUri=sagemaker_studio_user.sagemakerStudioUserUri)

        return sagemaker_studio_user

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    def update_sagemaker_studio_domain(environment, domain, data):
        SagemakerStudioService._update_sagemaker_studio_domain_vpc(environment.AwsAccountId, environment.region, data)
        domain.vpcType = data.get('vpcType')
        if data.get('vpcId'):
            domain.vpcId = data.get('vpcId')
        if data.get('subnetIds'):
            domain.subnetIds = data.get('subnetIds')

    @staticmethod
    def _update_sagemaker_studio_domain_vpc(account_id, region, data={}):
        cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(accountid=account_id, region=region)
        if data.get('vpcId', None):
            data['vpcType'] = 'imported'
        else:
            response = EC2.check_default_vpc_exists(
                AwsAccountId=account_id,
                region=region,
                role=cdk_look_up_role_arn,
            )
            if response:
                vpcId, subnetIds = response
                data['vpcType'] = 'default'
                data['vpcId'] = vpcId
                data['subnetIds'] = subnetIds
            else:
                data['vpcType'] = 'created'

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    def create_sagemaker_studio_domain(session, environment, data: dict = {}):
        SagemakerStudioService._update_sagemaker_studio_domain_vpc(environment.AwsAccountId, environment.region, data)

        domain = SageMakerStudioRepository.create_sagemaker_studio_domain(
            session=session,
            username=get_context().username,
            environment=environment,
            data=data,
        )
        return domain

    @staticmethod
    def get_environment_sagemaker_studio_domain(*, environment_uri: str):
        with _session() as session:
            return SageMakerStudioRepository.get_sagemaker_studio_domain_by_env_uri(session, env_uri=environment_uri)

    @staticmethod
    def list_sagemaker_studio_users(*, filter: dict) -> dict:
        with _session() as session:
            return SageMakerStudioRepository.paginated_sagemaker_studio_users(
                session=session,
                username=get_context().username,
                groups=get_context().groups,
                filter=filter,
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SGMSTUDIO_USER)
    def get_sagemaker_studio_user(*, uri: str):
        with _session() as session:
            return SagemakerStudioService._get_sagemaker_studio_user(session, uri)

    @staticmethod
    def get_sagemaker_studio_user_status(*, uri: str):
        with _session() as session:
            user = SagemakerStudioService._get_sagemaker_studio_user(session, uri)
            status = sagemaker_studio_client(user).get_sagemaker_studio_user_status()
            user.sagemakerStudioUserStatus = status
            return status

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    @ResourcePolicyService.has_resource_permission(SGMSTUDIO_USER_URL)
    def get_sagemaker_studio_user_presigned_url(*, uri: str):
        with _session() as session:
            user = SagemakerStudioService._get_sagemaker_studio_user(session, uri)
            return sagemaker_studio_client(user).get_sagemaker_studio_user_presigned_url()

    @staticmethod
    def get_sagemaker_studio_user_applications(*, uri: str):
        with _session() as session:
            user = SagemakerStudioService._get_sagemaker_studio_user(session, uri)
            return sagemaker_studio_client(user).get_sagemaker_studio_user_applications()

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    @ResourcePolicyService.has_resource_permission(DELETE_SGMSTUDIO_USER)
    def delete_sagemaker_studio_user(*, uri: str, delete_from_aws: bool):
        """Deletes SageMaker Studio user from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            user = SagemakerStudioService._get_sagemaker_studio_user(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, user.environmentUri)
            session.delete(user)

            ResourcePolicyService.delete_resource_policy(
                session=session,
                resource_uri=user.sagemakerStudioUserUri,
                group=user.SamlAdminGroupName,
            )

            if delete_from_aws:
                StackService.delete_stack(
                    target_uri=uri, accountid=env.AwsAccountId, cdk_role_arn=env.CDKRoleArn, region=env.region
                )
            return True

    @staticmethod
    def _get_sagemaker_studio_user(session, uri):
        user = SageMakerStudioRepository.find_sagemaker_studio_user(session=session, uri=uri)
        if not user:
            raise exceptions.ObjectNotFound('SagemakerStudioUser', uri)
        return user
