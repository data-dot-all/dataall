import logging
import os
import re

from sqlalchemy.orm import Query
from typing import List

from dataall.base.aws.ec2_client import EC2
from dataall.base.aws.iam import IAM
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.s3_client import S3_client
from dataall.base.utils import Parameter
from dataall.base.aws.sts import SessionHelper
from dataall.base.context import get_context
from dataall.base.db.exceptions import AWSResourceNotFound
from dataall.base.utils.consumption_principal_utils import EnvironmentIAMPrincipalType
from dataall.core.environment.db.environment_enums import PolicyManagementOptions
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.permissions.services.environment_permissions import (
    ENABLE_ENVIRONMENT_SUBSCRIPTIONS,
    CREDENTIALS_ENVIRONMENT,
)
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentParameter, ConsumptionPrincipal
from dataall.core.environment.db.environment_repositories import EnvironmentParameterRepository, EnvironmentRepository
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.core.permissions.db.permission.permission_models import PermissionType

from dataall.base.db.paginator import paginate
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.db import exceptions
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.api.enums import EnvironmentPermission, EnvironmentType
from dataall.core.stacks.aws.cloudformation import CloudFormation

from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTagRepository
from dataall.core.stacks.api.enums import StackStatus
from dataall.core.environment.services.managed_iam_policies import PolicyManager

from dataall.core.permissions.services.organization_permissions import LINK_ENVIRONMENT, GET_ORGANIZATION
from dataall.core.permissions.services import environment_permissions
from dataall.core.permissions.services.tenant_permissions import MANAGE_ENVIRONMENTS
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.vpc.db.vpc_repositories import VpcRepository
from dataall.modules.shares_base.services.shares_enums import PrincipalType

log = logging.getLogger(__name__)


class EnvironmentRequestValidationService:
    @staticmethod
    def validate_update_consumption_principal(data):
        if not data:
            raise exceptions.RequiredParameter('input')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('consumptionPrincipalName'):
            raise exceptions.RequiredParameter('consumptionPrincipalName')

    @staticmethod
    def validate_invite_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')

    @staticmethod
    def validate_creation_params(data, uri, session):
        EnvironmentRequestValidationService.validate_user_groups(data)
        if not uri:
            raise exceptions.RequiredParameter('organizationUri')
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('group')
        if not data.get('AwsAccountId'):
            raise exceptions.RequiredParameter('AwsAccountId')
        if not data.get('region'):
            raise exceptions.RequiredParameter('region')
        EnvironmentRequestValidationService.validate_resource_prefix(data)
        EnvironmentRequestValidationService.validate_account_region(data, session)
        EnvironmentRequestValidationService.validate_org_group(data['organizationUri'], data['SamlGroupName'], session)

    @staticmethod
    def validate_resource_prefix(data):
        if data.get('resourcePrefix') and not bool(re.match(r'^[a-z-]+$', data.get('resourcePrefix'))):
            raise exceptions.InvalidInput(
                'resourcePrefix',
                data.get('resourcePrefix'),
                'must match the pattern ^[a-z-]+$',
            )

    @staticmethod
    def validate_account_region(data, session):
        environment = EnvironmentRepository.find_environment_by_account_region(
            session=session, account_id=data.get('AwsAccountId'), region=data.get('region')
        )
        if environment:
            raise exceptions.InvalidInput(
                'AwsAccount/region',
                f'{data.get("AwsAccountId")}/{data.get("region")}',
                f'unique. An environment for {data.get("AwsAccountId")}/{data.get("region")} already exists',
            )

    @staticmethod
    def validate_user_groups(data):
        if data.get('SamlGroupName') and data.get('SamlGroupName') not in get_context().groups:
            raise exceptions.UnauthorizedOperation(
                action=LINK_ENVIRONMENT,
                message=f'User: {get_context().username} is not a member of the group {data["SamlGroupName"]}',
            )

    @staticmethod
    def validate_consumption_principal_params(data):
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('IAMPrincipalArn'):
            raise exceptions.RequiredParameter('IAMPrincipalArn')

    @staticmethod
    def validate_org_group(org_uri, group, session):
        if OrganizationRepository.find_group_membership(session, [group], org_uri) is None:
            raise Exception(
                f'Group {group} is not a member of the organization {org_uri}. '
                f'Invite this group to the organisation before giving it access to the environment.'
            )


class EnvironmentService:
    @staticmethod
    def _validate_permissions(session, uri, g_permissions, group):
        """
        g_permissions: coming from frontend = ENVIRONMENT_INVITATION_REQUEST

        """
        if environment_permissions.UPDATE_ENVIRONMENT_GROUP in g_permissions:
            g_permissions.append(environment_permissions.REMOVE_ENVIRONMENT_GROUP)

        g_permissions.extend(environment_permissions.ENVIRONMENT_INVITED_DEFAULT)
        g_permissions = list(set(g_permissions))

        if g_permissions not in environment_permissions.ENVIRONMENT_INVITED:
            exceptions.PermissionUnauthorized(action='INVITE_TEAM', group_name=group, resource_uri=uri)

        env_group_permissions = []
        for p in g_permissions:
            env_group_permissions.append(
                PermissionRepository.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )

    @staticmethod
    def _get_pivot_role_as_part_of_environment():
        ssm_param = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'),
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/pivotRole/enablePivotRoleAutoCreate',
        )
        return ssm_param == 'True'

    @staticmethod
    def _check_cdk_resources(account_id, region, data) -> str:
        """
        Check if all necessary cdk resources exists in the account
        :return : pivot role name
        """

        ENVNAME = os.environ.get('envname', 'local')
        print('ENVNAME = ', ENVNAME)
        if ENVNAME == 'pytest':
            return 'CdkRoleName'

        log.info('Checking cdk resources for environment.')

        pivot_role_as_part_of_environment = EnvironmentService._get_pivot_role_as_part_of_environment()
        log.info(f'Pivot role as part of environment = {pivot_role_as_part_of_environment}')

        cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(accountid=account_id, region=region)
        cdk_role_name = CloudFormation.check_existing_cdk_toolkit_stack(AwsAccountId=account_id, region=region)

        if not pivot_role_as_part_of_environment:
            log.info('Check if PivotRole exist in the account')
            pivot_role_arn = SessionHelper.get_delegation_role_arn(accountid=account_id, region=region)
            role = IAM.get_role(
                account_id=account_id, region=region, role_arn=pivot_role_arn, role=cdk_look_up_role_arn
            )
            if not role:
                raise exceptions.AWSResourceNotFound(
                    action='CHECK_PIVOT_ROLE',
                    message='Pivot Role has not been created in the Environment AWS Account',
                )

        mlStudioEnabled = None
        for parameter in data.get('parameters', []):
            if parameter['key'] == 'mlStudiosEnabled':
                mlStudioEnabled = parameter['value']

        if mlStudioEnabled and data.get('vpcId', None) and data.get('subnetIds', []):
            log.info('Check if ML Studio VPC Exists in the Account')
            EC2.check_vpc_exists(
                AwsAccountId=account_id,
                region=region,
                role=cdk_look_up_role_arn,
                vpc_id=data.get('vpcId', None),
                subnet_ids=data.get('subnetIds', []),
            )

        return cdk_role_name

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def get_trust_account(uri):
        return SessionHelper.get_account()

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def create_environment(uri, data=None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            EnvironmentRequestValidationService.validate_creation_params(data, uri, session)
            cdk_role_name = EnvironmentService._check_cdk_resources(data.get('AwsAccountId'), data.get('region'), data)
            env = Environment(
                organizationUri=data.get('organizationUri'),
                label=data.get('label', 'Unnamed'),
                tags=data.get('tags', []),
                owner=context.username,
                description=data.get('description', ''),
                environmentType=data.get('type', EnvironmentType.Data.value),
                AwsAccountId=data.get('AwsAccountId'),
                region=data.get('region'),
                SamlGroupName=data['SamlGroupName'],
                validated=False,
                isOrganizationDefaultEnvironment=False,
                EnvironmentDefaultIAMRoleName=data.get('EnvironmentDefaultIAMRoleArn', 'unknown').split('/')[-1],
                EnvironmentDefaultIAMRoleArn=data.get('EnvironmentDefaultIAMRoleArn', 'unknown'),
                CDKRoleArn=f'arn:aws:iam::{data.get("AwsAccountId")}:role/{cdk_role_name}',
                resourcePrefix=data.get('resourcePrefix'),
            )

            session.add(env)
            session.commit()

            EnvironmentService._update_env_parameters(session, env, data)
            EnvironmentResourceManager.create_env(session, env, data=data)

            env.EnvironmentDefaultBucketName = NamingConventionService(
                target_uri=env.environmentUri,
                target_label=env.label,
                pattern=NamingConventionPattern.S3,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()

            env.EnvironmentLogsBucketName = NamingConventionService(
                target_uri=env.environmentUri,
                target_label='env-access-logs',
                pattern=NamingConventionPattern.S3,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()

            env.EnvironmentDefaultAthenaWorkGroup = NamingConventionService(
                target_uri=env.environmentUri,
                target_label=env.label,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()

            if not data.get('EnvironmentDefaultIAMRoleArn'):
                env_role_name = NamingConventionService(
                    target_uri=env.environmentUri,
                    target_label=env.label,
                    pattern=NamingConventionPattern.IAM,
                    resource_prefix=env.resourcePrefix,
                ).build_compliant_name()
                env.EnvironmentDefaultIAMRoleName = env_role_name
                env.EnvironmentDefaultIAMRoleArn = f'arn:aws:iam::{env.AwsAccountId}:role/{env_role_name}'
                env.EnvironmentDefaultIAMRoleImported = False
            else:
                env.EnvironmentDefaultIAMRoleName = data['EnvironmentDefaultIAMRoleArn'].split('/')[-1]
                env.EnvironmentDefaultIAMRoleArn = data['EnvironmentDefaultIAMRoleArn']
                env.EnvironmentDefaultIAMRoleImported = True

            env_group = EnvironmentGroup(
                environmentUri=env.environmentUri,
                groupUri=data['SamlGroupName'],
                groupRoleInEnvironment=EnvironmentPermission.Owner.value,
                environmentIAMRoleArn=env.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=env.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup=env.EnvironmentDefaultAthenaWorkGroup,
            )
            session.add(env_group)
            ResourcePolicyService.attach_resource_policy(
                session=session,
                resource_uri=env.environmentUri,
                group=data['SamlGroupName'],
                permissions=environment_permissions.ENVIRONMENT_ALL,
                resource_type=Environment.__name__,
            )
            session.commit()

            activity = Activity(
                action='ENVIRONMENT:CREATE',
                label='ENVIRONMENT:CREATE',
                owner=context.username,
                summary=f'{context.username} linked environment {env.AwsAccountId} to organization {uri}',
                targetUri=env.environmentUri,
                targetType='env',
            )
            session.add(activity)
            return env

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.UPDATE_ENVIRONMENT)
    def update_environment(uri, data=None):
        EnvironmentRequestValidationService.validate_user_groups(data)
        EnvironmentRequestValidationService.validate_resource_prefix(data)

        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            previous_resource_prefix = environment.resourcePrefix
            EnvironmentService._check_cdk_resources(
                account_id=environment.AwsAccountId, region=environment.region, data=data
            )

            if data.get('label'):
                environment.label = data.get('label')
            if data.get('description'):
                environment.description = data.get('description', 'No description provided')
            if data.get('tags'):
                environment.tags = data.get('tags')
            if data.get('resourcePrefix'):
                environment.resourcePrefix = data.get('resourcePrefix')

            EnvironmentService._update_env_parameters(session, environment, data)

            ResourcePolicyService.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=environment.SamlGroupName,
                permissions=environment_permissions.ENVIRONMENT_ALL,
                resource_type=Environment.__name__,
            )
            return environment, previous_resource_prefix

    @staticmethod
    def _update_env_parameters(session, env: Environment, data):
        """Removes old parameters and creates new parameters associated with the environment"""
        params = data.get('parameters')
        if not params:
            return

        env_uri = env.environmentUri
        new_params = [EnvironmentParameter(env_uri, param.get('key'), param.get('value')) for param in params]
        EnvironmentParameterRepository(session).update_params(env_uri, new_params)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.INVITE_ENVIRONMENT_GROUP)
    def invite_group(uri, data=None) -> (Environment, EnvironmentGroup):
        EnvironmentRequestValidationService.validate_invite_params(data)
        group: str = data['groupUri']

        with get_context().db_engine.scoped_session() as session:
            EnvironmentService._validate_permissions(session, uri, data['permissions'], group)

            environment = EnvironmentService.get_environment_by_uri(session, uri)

            EnvironmentRequestValidationService.validate_org_group(environment.organizationUri, group, session)

            group_membership = EnvironmentService.find_environment_group(session, group, environment.environmentUri)
            if group_membership:
                raise exceptions.UnauthorizedOperation(
                    action='INVITE_TEAM',
                    message=f'Team {group} is already a member of the environment {environment.name}',
                )
            if data.get('environmentIAMRoleArn'):
                env_group_iam_role_arn = data['environmentIAMRoleArn']
                env_group_iam_role_name = data['environmentIAMRoleArn'].split('/')[-1]
                env_role_imported = True
            else:
                env_group_iam_role_name = NamingConventionService(
                    target_uri=environment.environmentUri,
                    target_label=group,
                    pattern=NamingConventionPattern.IAM,
                    resource_prefix=environment.resourcePrefix,
                ).build_compliant_name()
                env_group_iam_role_arn = f'arn:aws:iam::{environment.AwsAccountId}:role/{env_group_iam_role_name}'
                env_role_imported = False

            # If environment role is imported, then data.all should attach the policies at import time ( Fully Managed )
            # If environment role is created in environment stack, then data.all should attach the policies in the env stack ( Partially Managed - Here policy will be created but won't be attached )
            policy_management: str = (
                PolicyManagementOptions.FULLY_MANAGED.value
                if env_role_imported is True
                else PolicyManagementOptions.PARTIALLY_MANAGED.value
            )
            PolicyManager(
                session=session,
                account=environment.AwsAccountId,
                region=environment.region,
                environmentUri=environment.environmentUri,
                resource_prefix=environment.resourcePrefix,
                principal_name=env_group_iam_role_name,
            ).create_all_policies(policy_management=policy_management)

            athena_workgroup = NamingConventionService(
                target_uri=environment.environmentUri,
                target_label=group,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name()

            environment_group = EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group,
                invitedBy=get_context().username,
                environmentIAMRoleName=env_group_iam_role_name,
                environmentIAMRoleArn=env_group_iam_role_arn,
                environmentIAMRoleImported=env_role_imported,
                environmentAthenaWorkGroup=athena_workgroup,
            )
            session.add(environment_group)
            session.commit()
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                permissions=data['permissions'],
                resource_type=Environment.__name__,
            )

            return environment, environment_group

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.REMOVE_ENVIRONMENT_GROUP)
    def remove_group(uri, group):
        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            if group == environment.SamlGroupName:
                raise exceptions.UnauthorizedOperation(
                    action='REMOVE_TEAM',
                    message=f'Team: {group} is the owner of the environment {environment.name}',
                )

            group_env_objects_count = EnvironmentResourceManager.count_group_resources(
                session=session, environment=environment, group_uri=group
            )

            if group_env_objects_count > 0:
                raise exceptions.EnvironmentResourcesFound(
                    action='Remove Team',
                    message=f'Team: {group} has created {group_env_objects_count} resources on this environment.',
                )

            group_env_consumption_roles = EnvironmentRepository.query_user_environment_consumption_principals(
                session, [group], uri, {}
            ).all()
            if group_env_consumption_roles:
                raise exceptions.EnvironmentResourcesFound(
                    action='Remove Team',
                    message=f'Team: {group} has consumption role(s) on this environment.',
                )

            group_membership = EnvironmentService.find_environment_group(session, group, environment.environmentUri)

            PolicyManager(
                session=session,
                account=environment.AwsAccountId,
                region=environment.region,
                environmentUri=environment.environmentUri,
                resource_prefix=environment.resourcePrefix,
                principal_name=group_membership.environmentIAMRoleName,
            ).delete_all_policies()

            if group_membership:
                session.delete(group_membership)
                session.commit()

            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                resource_type=Environment.__name__,
            )
            return environment

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.UPDATE_ENVIRONMENT_GROUP)
    def update_group_permissions(uri, data=None):
        EnvironmentRequestValidationService.validate_invite_params(data)

        group = data['groupUri']

        with get_context().db_engine.scoped_session() as session:
            EnvironmentService._validate_permissions(session, uri, data['permissions'], group)

            environment = EnvironmentService.get_environment_by_uri(session, uri)

            group_membership = EnvironmentService.find_environment_group(session, group, environment.environmentUri)
            if not group_membership:
                raise exceptions.UnauthorizedOperation(
                    action='UPDATE_TEAM_ENVIRONMENT_PERMISSIONS',
                    message=f'Team {group.name} is not a member of the environment {environment.name}',
                )

            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                resource_type=Environment.__name__,
            )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                permissions=data['permissions'],
                resource_type=Environment.__name__,
            )
            return environment

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUP_PERMISSIONS)
    def list_group_permissions(uri, group_uri):
        # the permission checked
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentService.list_group_permissions_internal(session, uri, group_uri)

    @staticmethod
    def list_group_permissions_internal(session, uri, group_uri):
        """No permission check, only for internal usages"""
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        return ResourcePolicyService.get_resource_policy_permissions(
            session=session,
            group_uri=group_uri,
            resource_uri=environment.environmentUri,
        )

    @staticmethod
    def list_group_invitation_permissions():
        with get_context().db_engine.scoped_session() as session:
            group_invitation_permissions = []
            for p in environment_permissions.ENVIRONMENT_INVITATION_REQUEST:
                group_invitation_permissions.append(
                    PermissionRepository.find_permission_by_name(
                        session=session,
                        permission_name=p,
                        permission_type=PermissionType.RESOURCE.name,
                    )
                )
            return group_invitation_permissions

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.ADD_ENVIRONMENT_CONSUMPTION_ROLES)
    def add_consumption_principal(uri, data=None) -> (Environment, EnvironmentGroup):
        EnvironmentRequestValidationService.validate_consumption_principal_params(data)

        group: str = data['groupUri']
        IAMPrincipalArn: str = data['IAMPrincipalArn']

        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            consumptionType = EnvironmentIAMPrincipalType.get_consumption_type(IAMPrincipalARN=IAMPrincipalArn)

            principal = None
            if consumptionType == EnvironmentIAMPrincipalType.ROLE.value:
                principal = IAM.get_role(environment.AwsAccountId, environment.region, IAMPrincipalArn)
            elif consumptionType == EnvironmentIAMPrincipalType.USER.value:
                principal = IAM.get_user(environment.AwsAccountId, environment.region, IAMPrincipalArn)

            if not principal:
                raise exceptions.AWSResourceNotFound(
                    action='ADD_CONSUMPTION_ROLE',
                    message=f'{IAMPrincipalArn} does not exist in this account',
                )

            alreadyAdded = EnvironmentRepository.find_consumption_principals_by_IAMArn(
                session, environment.environmentUri, IAMPrincipalArn
            )
            if alreadyAdded:
                raise exceptions.UnauthorizedOperation(
                    action='ADD_CONSUMPTION_ROLE',
                    message=f'IAM principal {IAMPrincipalArn} is already added to the environment {environment.name}',
                )

            consumption_principal = ConsumptionPrincipal(
                consumptionPrincipalName=data['consumptionPrincipalName'],
                environmentUri=environment.environmentUri,
                groupUri=group,
                IAMPrincipalArn=IAMPrincipalArn,
                IAMPrincipalName=IAMPrincipalArn.split('/')[-1],
                dataallManaged=data.get('dataallManaged'),
                consumptionPrincipalType=consumptionType,
            )

            PolicyManager(
                session=session,
                account=environment.AwsAccountId,
                region=environment.region,
                environmentUri=environment.environmentUri,
                resource_prefix=environment.resourcePrefix,
                principal_name=consumption_principal.IAMPrincipalName,
                principal_type=consumptionType,
            ).create_all_policies(policy_management=consumption_principal.dataallManaged)

            session.add(consumption_principal)
            session.commit()

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=consumption_principal.consumptionPrincipalUri,
                permissions=environment_permissions.CONSUMPTION_ROLE_ALL,
                resource_type=ConsumptionPrincipal.__name__,
            )
            return consumption_principal

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def remove_consumption_principal(uri, env_uri):
        with get_context().db_engine.scoped_session() as session:
            consumption_principal = EnvironmentService.get_environment_consumption_principal(session, uri, env_uri)
            environment = EnvironmentService.get_environment_by_uri(session, env_uri)

            num_resources = EnvironmentResourceManager.count_consumption_role_resources(session, uri)
            if num_resources > 0:
                raise exceptions.EnvironmentResourcesFound(
                    action='Remove Consumption Principal',
                    message=f'Consumption principal: {consumption_principal.consumptionPrincipalName} has created {num_resources} resources on this environment.',
                )

            if consumption_principal:
                PolicyManager(
                    session=session,
                    account=environment.AwsAccountId,
                    region=environment.region,
                    environmentUri=environment.environmentUri,
                    resource_prefix=environment.resourcePrefix,
                    principal_name=consumption_principal.IAMPrincipalName,
                    principal_type=consumption_principal.consumptionPrincipalType,
                ).delete_all_policies()

                ResourcePolicyService.delete_resource_policy(
                    session=session,
                    group=consumption_principal.groupUri,
                    resource_uri=consumption_principal.consumptionPrincipalUri,
                    resource_type=ConsumptionPrincipal.__name__,
                )

                session.delete(consumption_principal)
                session.commit()

            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def update_consumption_principal(uri, env_uri, input):
        EnvironmentRequestValidationService.validate_update_consumption_principal(input)
        with get_context().db_engine.scoped_session() as session:
            consumption_principal = EnvironmentService.get_environment_consumption_principal(session, uri, env_uri)
            if consumption_principal:
                ResourcePolicyService.update_resource_policy(
                    session=session,
                    resource_uri=uri,
                    resource_type=ConsumptionPrincipal.__name__,
                    old_group=consumption_principal.groupUri,
                    new_group=input['groupUri'],
                    new_permissions=environment_permissions.CONSUMPTION_ROLE_ALL,
                )
                for key, value in input.items():
                    setattr(consumption_principal, key, value)
                session.commit()

                # If the input consumption role is not Fully-Managed then attach the share policy if it exists
                if consumption_principal.dataallManaged == PolicyManagementOptions.FULLY_MANAGED.value:
                    environment: Environment = EnvironmentService.get_environment_by_uri(session, env_uri)
                    share_policy_manager = PolicyManager(
                        session=session,
                        account=environment.AwsAccountId,
                        region=environment.region,
                        environmentUri=environment.environmentUri,
                        resource_prefix=environment.resourcePrefix,
                        principal_name=consumption_principal.IAMPrincipalName,
                        principal_type=consumption_principal.consumptionPrincipalType,
                    )
                    for policy_manager in [
                        Policy
                        for Policy in share_policy_manager.initializedPolicies
                        if Policy.policy_type == 'SharePolicy'
                    ]:
                        managed_policy_list = policy_manager.get_policies_unattached_to_principal()
                        policy_manager.attach_policies(managed_policy_list)

            return consumption_principal

    @staticmethod
    def paginated_user_environments(data=None) -> dict:
        context = get_context()
        data = data if data is not None else {}
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environments(session, context.username, context.groups, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    def list_valid_user_environments(data=None) -> dict:
        context = get_context()
        data = data if data is not None else {}
        with context.db_engine.scoped_session() as session:
            query = EnvironmentRepository.query_user_environments(session, context.username, context.groups, data)
            valid_environments = []
            valid_statuses = [
                StackStatus.CREATE_COMPLETE.value,
                StackStatus.UPDATE_COMPLETE.value,
                StackStatus.UPDATE_ROLLBACK_COMPLETE.value,
            ]
            for env in query:
                if StackRepository.find_stack_by_target_uri(session, env.environmentUri, valid_statuses):
                    valid_environments.append(env)

            return {
                'count': len(valid_environments),
                'nodes': valid_environments,
            }

    @staticmethod
    def paginated_user_groups(data=None) -> dict:
        context = get_context()
        data = data if data is not None else {}
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_groups(session, context.username, context.groups, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    def paginated_user_consumption_principals(data=None) -> dict:
        context = get_context()
        data = data if data is not None else {}
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_consumption_principals(
                    session, context.username, context.groups, data
                ),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_user_environment_groups(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environment_groups(session, get_context().groups, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 1000),
            ).to_dict()

    @staticmethod
    def get_all_environment_groups(session, uri, filter) -> Query:
        return EnvironmentRepository.query_all_environment_groups(session, uri, filter)

    @staticmethod
    def list_all_environment_groups(uri, data=None) -> [str]:
        with get_context().db_engine.scoped_session() as session:
            return [g.groupUri for g in EnvironmentRepository.query_all_environment_groups(session, uri, data).all()]

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_all_environment_groups(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentService.get_all_environment_groups(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def list_environment_groups(session, uri) -> [str]:
        return [
            g.groupUri
            for g in EnvironmentRepository.query_user_environment_groups(session, get_context().groups, uri, {}).all()
        ]

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_environment_invited_groups(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_environment_invited_groups(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def list_environment_invited_groups(session, uri):
        return EnvironmentRepository.query_environment_invited_groups(session, uri, {}).all()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_user_environment_consumption_principals(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environment_consumption_principals(
                    session, get_context().groups, uri, data
                ),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 1000),
            ).to_dict()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_all_environment_consumption_principals(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_all_environment_consumption_principals(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def get_consumption_role(session, uri) -> Query:
        return EnvironmentRepository.get_consumption_role(session, uri)

    @staticmethod
    def get_role_policy_management_type(principal_type: str, principal_id: str):
        with get_context().db_engine.scoped_session() as session:
            if principal_type == PrincipalType.ConsumptionRole.value:
                consumption_role: ConsumptionPrincipal = EnvironmentService.get_consumption_role(
                    session, uri=principal_id
                )
                return consumption_role.dataallManaged

        return PolicyManagementOptions.FULLY_MANAGED.value

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_NETWORKS)
    def paginated_environment_networks(uri, data=None) -> dict:
        data = data if data is not None else {}
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=VpcRepository.query_environment_networks(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def find_environment_group(session, group_uri, environment_uri):
        try:
            env_group = EnvironmentService.get_environment_group(session, group_uri, environment_uri)
            return env_group
        except Exception:
            return None

    @staticmethod
    def get_environment_group(session, group_uri, environment_uri) -> EnvironmentGroup:
        env_group = EnvironmentRepository.get_environment_group(session, group_uri, environment_uri)
        if not env_group:
            raise exceptions.ObjectNotFound('EnvironmentGroup', f'({group_uri},{environment_uri})')
        return env_group

    @staticmethod
    def get_environment_consumption_principal(session, principal_uri, environment_uri) -> ConsumptionPrincipal:
        consumption_principal = EnvironmentRepository.get_environment_consumption_principal(
            session, principal_uri, environment_uri
        )
        if not consumption_principal:
            raise exceptions.ObjectNotFound('ConsumptionPrincipalUri', f'({principal_uri},{environment_uri})')
        return consumption_principal

    @staticmethod
    def get_environment_by_uri(session, uri) -> Environment:
        return EnvironmentRepository.get_environment_by_uri(session, uri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.GET_ENVIRONMENT)
    def find_environment_by_uri(uri) -> Environment:
        return EnvironmentService.find_environment_by_uri_simplified(uri)

    @staticmethod
    def find_environment_by_uri_simplified(uri):
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentService.get_environment_by_uri(session, uri)

    @staticmethod
    def list_all_active_environments(session) -> List[Environment]:
        """
        Lists all active dataall environments
        :param session:
        :return: [Environment]
        """
        environments: [Environment] = EnvironmentRepository.query_all_active_environments(session)
        log.info(f'Retrieved all active dataall environments {[e.AwsAccountId for e in environments]}')
        return environments

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.DELETE_ENVIRONMENT)
    def delete_environment(uri):
        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            env_groups = EnvironmentRepository.query_environment_groups(session, uri)
            env_consumption_principals = EnvironmentRepository.query_all_environment_consumption_principals(
                session, uri, None
            )

            env_resources = 0
            for group in env_groups:
                env_resources += EnvironmentResourceManager.count_group_resources(session, environment, group.groupUri)
            for principal in env_consumption_principals:
                env_resources += EnvironmentResourceManager.count_consumption_role_resources(
                    session, principal.consumptionPrincipalUri
                )

            if env_resources > 0:
                raise exceptions.EnvironmentResourcesFound(
                    action='Delete Environment',
                    message=f'Found {env_resources} resources on environment {environment.label} - Delete all environment '
                    f'related objects before proceeding',
                )
            else:
                if StackRepository.find_stack_by_target_uri(session, environment.environmentUri) not in [
                    StackStatus.ROLLBACK_COMPLETE.value,
                    StackStatus.ROLLBACK_IN_PROGRESS.value,
                    StackStatus.CREATE_FAILED.value,
                    StackStatus.DELETE_COMPLETE.value,
                ]:
                    PolicyManager(
                        session=session,
                        account=environment.AwsAccountId,
                        region=environment.region,
                        environmentUri=environment.environmentUri,
                        resource_prefix=environment.resourcePrefix,
                        principal_name=environment.EnvironmentDefaultIAMRoleName,
                    ).delete_all_policies()

                KeyValueTagRepository.delete_key_value_tags(session, environment.environmentUri, 'environment')
                EnvironmentResourceManager.delete_env(session, environment)
                EnvironmentParameterRepository(session).delete_params(environment.environmentUri)

                for group in env_groups:
                    session.delete(group)

                    ResourcePolicyService.delete_resource_policy(
                        session=session,
                        resource_uri=uri,
                        group=group.groupUri,
                    )

                for principal in env_consumption_principals:
                    session.delete(principal)

                return session.delete(environment), environment

    @staticmethod
    def get_environment_parameters(env_uri):
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentParameterRepository(session).get_params(env_uri)

    @staticmethod
    def get_boolean_env_param(session, env: Environment, param: str) -> bool:
        param = EnvironmentParameterRepository(session).get_param(env.environmentUri, param)
        return param is not None and param.value.lower() == 'true'

    @staticmethod
    def _is_user_invited(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return EnvironmentRepository.is_user_invited_to_environment(session=session, groups=context.groups, uri=uri)

    @staticmethod
    def resolve_user_role(environment: Environment):
        if environment.owner == get_context().username:
            return EnvironmentPermission.Owner.value
        elif environment.SamlGroupName in get_context().groups:
            return EnvironmentPermission.Admin.value
        elif EnvironmentService._is_user_invited(environment.environmentUri):
            return EnvironmentPermission.Invited.value
        return EnvironmentPermission.NotInvited.value

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(ENABLE_ENVIRONMENT_SUBSCRIPTIONS)
    def enable_subscriptions(uri, input: dict = None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            if input.get('producersTopicArn'):
                environment.subscriptionsProducersTopicName = input.get('producersTopicArn')
                environment.subscriptionsProducersTopicImported = True

            else:
                environment.subscriptionsProducersTopicName = NamingConventionService(
                    target_label=f'{environment.label}-producers-topic',
                    target_uri=environment.environmentUri,
                    pattern=NamingConventionPattern.DEFAULT,
                    resource_prefix=environment.resourcePrefix,
                ).build_compliant_name()

            environment.subscriptionsConsumersTopicName = NamingConventionService(
                target_label=f'{environment.label}-consumers-topic',
                target_uri=environment.environmentUri,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name()
            environment.subscriptionsConsumersTopicImported = False
            environment.subscriptionsEnabled = True
            session.commit()
            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(ENABLE_ENVIRONMENT_SUBSCRIPTIONS)
    def disable_subscriptions(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            environment.subscriptionsConsumersTopicName = None
            environment.subscriptionsConsumersTopicImported = False
            environment.subscriptionsProducersTopicName = None
            environment.subscriptionsProducersTopicImported = False
            environment.subscriptionsEnabled = False
            session.commit()
            return True

    @staticmethod
    def _get_environment_group_aws_session(session, username, groups, environment, groupUri=None):
        if groupUri and groupUri not in groups:
            raise exceptions.UnauthorizedOperation(
                action='ENVIRONMENT_AWS_ACCESS',
                message=f'User: {username} is not member of the team {groupUri}',
            )
        pivot_session = SessionHelper.remote_session(environment.AwsAccountId, environment.region)
        if not groupUri:
            if environment.SamlGroupName in groups:
                aws_session = SessionHelper.get_session(
                    base_session=pivot_session,
                    role_arn=environment.EnvironmentDefaultIAMRoleArn,
                )
            else:
                raise exceptions.UnauthorizedOperation(
                    action='ENVIRONMENT_AWS_ACCESS',
                    message=f'User: {username} is not member of the environment admins team {environment.SamlGroupName}',
                )
        else:
            env_group = EnvironmentService.get_environment_group(
                session, group_uri=groupUri, environment_uri=environment.environmentUri
            )
            if not env_group:
                raise exceptions.UnauthorizedOperation(
                    action='ENVIRONMENT_AWS_ACCESS',
                    message=f'Team {groupUri} is not invited to the environment {environment.name}',
                )
            else:
                aws_session = SessionHelper.get_session(
                    base_session=pivot_session,
                    role_arn=env_group.environmentIAMRoleArn,
                )
            if not aws_session:
                raise exceptions.AWSResourceNotFound(
                    action='ENVIRONMENT_AWS_ACCESS',
                    message=f'Failed to start an AWS session on environment {environment.AwsAccountId}',
                )
        return aws_session

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(CREDENTIALS_ENVIRONMENT)
    def get_environment_assume_role_url(uri, groupUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            url = SessionHelper.get_console_access_url(
                EnvironmentService._get_environment_group_aws_session(
                    session=session,
                    username=context.username,
                    groups=context.groups,
                    environment=environment,
                    groupUri=groupUri,
                ),
                region=environment.region,
            )
            return url

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(CREDENTIALS_ENVIRONMENT)
    def generate_environment_access_token(uri, groupUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            c = EnvironmentService._get_environment_group_aws_session(
                session=session,
                username=context.username,
                groups=context.groups,
                environment=environment,
                groupUri=groupUri,
            ).get_credentials()
            return {
                'AccessKey': c.access_key,
                'SessionKey': c.secret_key,
                'sessionToken': c.token,
            }

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def get_pivot_role(uri):
        pivot_role_name = SessionHelper.get_delegation_role_name(region='<REGION>')
        if not pivot_role_name:
            raise exceptions.AWSResourceNotFound(
                action='GET_PIVOT_ROLE_NAME',
                message='Pivot role name could not be found on AWS Systems Manager - Parameter Store',
            )
        return pivot_role_name

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def get_external_id(uri):
        external_id = SessionHelper.get_external_id_secret()
        if not external_id:
            raise exceptions.AWSResourceNotFound(
                action='GET_EXTERNAL_ID',
                message='External Id could not be found on AWS Secretsmanager',
            )
        return external_id

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def get_template_from_resource_bucket(uri, template_name):
        envname = os.getenv('envname', 'local')
        region = os.getenv('AWS_REGION', 'eu-central-1')

        resource_bucket = Parameter().get_parameter(env=envname, path='s3/resources_bucket_name')
        template_key = Parameter().get_parameter(env=envname, path=f's3/{template_name}')
        if not resource_bucket or not template_key:
            raise AWSResourceNotFound(
                action='GET_TEMPLATE',
                message=f'{template_name} Yaml template file could not be found on Amazon S3 bucket',
            )

        return S3_client.get_presigned_url(region, resource_bucket, template_key)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.GET_ENVIRONMENT)
    def resolve_consumption_principal_policies(uri, IAMPrincipalName, IAMPrincipalType):
        environment = EnvironmentService.find_environment_by_uri(uri=uri)
        with get_context().db_engine.scoped_session() as session:
            return PolicyManager(
                session=session,
                account=environment.AwsAccountId,
                region=environment.region,
                environmentUri=uri,
                resource_prefix=environment.resourcePrefix,
                principal_name=IAMPrincipalName,
                principal_type=IAMPrincipalType,
            ).get_all_policies()
