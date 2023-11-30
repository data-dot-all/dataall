"""
A service layer for ml studio
Central part for working with ml studio
"""
import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.base.context import get_context
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions import permissions
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.base.db import exceptions
from dataall.modules.mlstudio.aws.sagemaker_studio_client import sagemaker_studio_client, get_sagemaker_studio_domain
from dataall.modules.mlstudio.db.mlstudio_repositories import SageMakerStudioRepository
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser
from dataall.modules.mlstudio.aws.ec2_client import EC2
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
    return get_context().db_engine.scoped_session()


class SagemakerStudioService:
    """
    Encapsulate the logic of interactions with sagemaker ml studio.
    """
    @staticmethod
    @has_tenant_permission(MANAGE_SGMSTUDIO_USERS)
    @has_resource_permission(CREATE_SGMSTUDIO_USER)
    @has_group_permission(CREATE_SGMSTUDIO_USER)
    def create_sagemaker_studio_user(*, uri: str, admin_group: str, request: SagemakerStudioCreationRequest):
        """
        Creates an ML Studio user
        Throws an exception if ML Studio is not enabled for the environment
        Throws an exception if a SageMaker domain is not found
        """
        with _session() as session:
            env = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, env, "mlStudiosEnabled")

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_SGMSTUDIO_USER,
                    message=f'ML Studio feature is disabled for the environment {env.label}',
                )
            # FOR OLD ONES
            response = get_sagemaker_studio_domain(
                AwsAccountId=env.AwsAccountId,
                region=env.region
            )

            # FOR NEW ONES (default, created, imported)
            # - CHECK RDS FIRST
            # - IF NOT BOTO3

            existing_domain = response.get('DomainId', False)

            if not existing_domain:
                raise exceptions.AWSResourceNotAvailable(
                    action='Sagemaker Studio domain',
                    message='Update the environment stack '
                            'or create a Sagemaker studio domain on your AWS account.',
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
            SageMakerStudioRepository(session).save_sagemaker_studio_user(user=sagemaker_studio_user)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=SGMSTUDIO_USER_ALL,
                resource_uri=sagemaker_studio_user.sagemakerStudioUserUri,
                resource_type=SagemakerStudioUser.__name__,
            )

            if env.SamlGroupName != sagemaker_studio_user.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=SGMSTUDIO_USER_ALL,
                    resource_uri=sagemaker_studio_user.sagemakerStudioUserUri,
                    resource_type=SagemakerStudioUser.__name__,
                )

            Stack.create_stack(
                session=session,
                environment_uri=sagemaker_studio_user.environmentUri,
                target_type='mlstudio',
                target_uri=sagemaker_studio_user.sagemakerStudioUserUri,
                target_label=sagemaker_studio_user.label,
            )

        stack_helper.deploy_stack(targetUri=sagemaker_studio_user.sagemakerStudioUserUri)

        return sagemaker_studio_user

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.UPDATE_ENVIRONMENT)
    def create_sagemaker_studio_domain(*, uri: str, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, environment, "mlStudiosEnabled")
            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=permissions.UPDATE_ENVIRONMENT,
                    message=f'ML Studio feature is disabled for the environment {environment.label}',
                )
            cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
                accountid=environment.AwsAccountId, region=environment.region
            )
            if data.get("vpcId", None):
                SagemakerStudioService.check_mlstudio_domain_vpc(
                    account_id=environment.AwsAccountId,
                    region=environment.region,
                    cdk_look_up_role_arn=cdk_look_up_role_arn,
                    data=data
                )
                data["vpcType"] = "imported"
            elif EC2.check_default_vpc_exists(
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                role=cdk_look_up_role_arn,
            ):
                data["vpcType"] = "default"
            else:
                data["vpcType"] = "created"

            domain = SageMakerStudioRepository(session).create_sagemaker_studio_domain(
                username=get_context().username,
                environment=environment,
                data=data,
            )
            # TODO: DEPLOY ENV STACK
        return domain

    @staticmethod
    def check_mlstudio_domain_vpc(account_id: str, region: str, cdk_look_up_role_arn: str, data: dict):
        if data.get("vpcId", None) and data.get("subnetIds", None):
            EC2.check_vpc_exists(
                AwsAccountId=account_id,
                region=region,
                role=cdk_look_up_role_arn,
                vpc_id=data.get("vpcId", None),
                subnet_ids=data.get('subnetIds', []),
            )
            data["vpcType"] = "imported"
            return True

    @staticmethod
    def _get_domain_env_uri(session, uri):
        domain = SagemakerStudioService._get_sagemaker_studio_domain(session, uri)
        return domain.environmentUri

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.UPDATE_ENVIRONMENT, parent_resource=_get_domain_env_uri)
    def delete_sagemaker_studio_domain(*, uri: str):
        with _session() as session:
            domain = SagemakerStudioService._get_sagemaker_studio_domain(session, uri)
            # TODO: CHECK NUMBER OF USERS BEFORE DELETE
            session.delete(domain)
            # TODO: DEPLOY ENV STACK
            return True

    @staticmethod
    def list_environment_sagemaker_studio_domains(*, filter: dict, environment_uri: str) -> dict:
        with _session() as session:
            return SageMakerStudioRepository(session).paginated_environment_sagemaker_studio_domains(
                uri=environment_uri,
                filter=filter,
            )

    @staticmethod
    def list_sagemaker_studio_users(*, filter: dict) -> dict:
        with _session() as session:
            return SageMakerStudioRepository(session).paginated_sagemaker_studio_users(
                username=get_context().username,
                groups=get_context().groups,
                filter=filter,
            )

    @staticmethod
    @has_resource_permission(GET_SGMSTUDIO_USER)
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
    @has_resource_permission(SGMSTUDIO_USER_URL)
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
    @has_resource_permission(DELETE_SGMSTUDIO_USER)
    def delete_sagemaker_studio_user(*, uri: str, delete_from_aws: bool):
        """Deletes SageMaker Studio user from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            user = SagemakerStudioService._get_sagemaker_studio_user(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, user.environmentUri)
            session.delete(user)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=user.sagemakerStudioUserUri,
                group=user.SamlAdminGroupName,
            )

            if delete_from_aws:
                stack_helper.delete_stack(
                    target_uri=uri,
                    accountid=env.AwsAccountId,
                    cdk_role_arn=env.CDKRoleArn,
                    region=env.region
                )
            return True

    @staticmethod
    def _get_sagemaker_studio_user(session, uri):
        user = SageMakerStudioRepository(session).find_sagemaker_studio_user(uri=uri)
        if not user:
            raise exceptions.ObjectNotFound('SagemakerStudioUser', uri)
        return user
    
    @staticmethod
    def _get_sagemaker_studio_domain(session, uri):
        domain = SageMakerStudioRepository(session).find_sagemaker_studio_domain(uri=uri)
        if not domain:
            raise exceptions.ObjectNotFound('SagemakerStudioDomain', uri)
        return domain

