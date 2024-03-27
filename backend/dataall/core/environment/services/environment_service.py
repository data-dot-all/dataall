import json
import logging
import re

from dataall.base.aws.ec2_client import EC2
from dataall.base.aws.iam import IAM
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.sts import SessionHelper
from dataall.base.context import get_context
from dataall.core.stacks.api import stack_helper
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentParameter, ConsumptionRole
from dataall.core.environment.db.environment_repositories import (
    EnvironmentParameterRepository,
    EnvironmentRepository,
    EnvironmentGroupRepository,
)
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.core.permissions.db.permission_repositories import Permission
from dataall.core.permissions.db.permission_models import PermissionType
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.stacks.aws.cloudformation import CloudFormation
from dataall.base.db.paginator import paginate
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.db import exceptions
from dataall.core.permissions import permissions
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.api.enums import EnvironmentPermission, EnvironmentType

from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_models import Stack
from dataall.core.stacks.db.enums import StackStatus
from dataall.core.environment.services.managed_iam_policies import PolicyManager

log = logging.getLogger(__name__)


class EnvironmentPermissionsValidationService:

    @staticmethod
    def validate_permissions(session, uri, g_permissions, group):
        """
        g_permissions: coming from frontend = ENVIRONMENT_INVITATION_REQUEST

        """
        if permissions.INVITE_ENVIRONMENT_GROUP in g_permissions:
            g_permissions.append(permissions.REMOVE_ENVIRONMENT_GROUP)

        g_permissions.extend(permissions.ENVIRONMENT_INVITED_DEFAULT)
        g_permissions = list(set(g_permissions))

        if g_permissions not in permissions.ENVIRONMENT_INVITED:
            exceptions.PermissionUnauthorized(action='INVITE_TEAM', group_name=group, resource_uri=uri)

        env_group_permissions = []
        for p in g_permissions:
            env_group_permissions.append(
                Permission.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )

    @staticmethod
    def validate_group_membership(samlGroupName, groups, username):
        if samlGroupName and samlGroupName not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.LINK_ENVIRONMENT,
                message=f'User: {username} is not a member of the group {samlGroupName}',
            )


class EnvironmentRequestValidationService:
    @staticmethod
    def validate_creation_params(data, uri):
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
        EnvironmentRequestValidationService.validate_account_region(data)

    @staticmethod
    def validate_resource_prefix(data):
        if data.get('resourcePrefix') and not bool(re.match(r'^[a-z-]+$', data.get('resourcePrefix'))):
            raise exceptions.InvalidInput(
                'resourcePrefix',
                data.get('resourcePrefix'),
                'must match the pattern ^[a-z-]+$',
            )

    @staticmethod
    def validate_account_region(data):
        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentRepository.find_environment_by_account_region(
                session=session, account_id=data.get('AwsAccountId'), region=data.get('region')
            )
            if environment:
                raise exceptions.InvalidInput(
                    'AwsAccount/region',
                    f"{data.get('AwsAccountId')}/{data.get('region')}",
                    f"unique. An environment for {data.get('AwsAccountId')}/{data.get('region')} already exists",
                )

    @staticmethod
    def validate_add_consumption_role_params(data):

        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('IAMRoleArn'):
            raise exceptions.RequiredParameter('IAMRoleArn')
        if not data.get('consumptionRoleName'):
            raise exceptions.RequiredParameter('consumptionRoleName')

    @staticmethod
    def validate_update_consumption_role_params(data):
        if not data:
            raise exceptions.RequiredParameter('input')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('consumptionRoleName'):
            raise exceptions.RequiredParameter('consumptionRoleName')

    @staticmethod
    def validate_invite_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')
        if not data.get('environmentUri'):
            raise exceptions.RequiredParameter('environmentUri')


class EnvironmentService:
    @staticmethod
    def check_environment(data):
        """Checks necessary resources for environment deployment.
        - Check CDKToolkit exists in Account assuming cdk_look_up_role
        - Check Pivot Role exists in Account if pivot_role_as_part_of_environment is False
        """

        account_id = data.get('AwsAccountId')
        region = data.get('region')

        pivot_role_as_part_of_environment = ParameterStoreManager.get_pivot_role_as_part_of_environment()
        log.info(f'Check environment. Pivot role as part of environment = {pivot_role_as_part_of_environment}')

        cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(accountid=account_id, region=region)

        if not pivot_role_as_part_of_environment:
            log.info('Check if PivotRole exist in the account')
            pivot_role_arn = SessionHelper.get_delegation_role_arn(accountid=account_id)
            role = IAM.get_role(account_id=account_id, role_arn=pivot_role_arn, role=cdk_look_up_role_arn)
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

    @staticmethod
    def get_enviromment_groups_from_list(session, envUri, groups):
        return EnvironmentGroupRepository.get_group_by_uri_from_group_list(session, envUri, groups)

    @staticmethod
    def _get_enviromment_group_by_uri(session, envUri, groupUri):
        return EnvironmentGroupRepository.get_group_by_uri(session, envUri, groupUri)

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.LINK_ENVIRONMENT)
    def create_environment(uri, data=None):
        context = get_context()

        EnvironmentRequestValidationService.validate_creation_params(data, uri)
        EnvironmentService.check_environment(data)

        with context.db_engine.scoped_session() as session:

            cdk_role_name = CloudFormation.check_existing_cdk_toolkit_stack(AwsAccountId=data.get('AwsAccountId'),
                                                                            region=data.get('region'))

            organization = OrganizationRepository.get_organization_by_uri(session, uri)
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
                CDKRoleArn=f"arn:aws:iam::{data.get('AwsAccountId')}:role/{cdk_role_name}",
                resourcePrefix=data.get('resourcePrefix'),
            )
            # userRoleInEnvironment -- query expression, can not be set via constructor
            env.userRoleInEnvironment = EnvironmentPermission.Owner.value

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
            ResourcePolicy.attach_resource_policy(
                session=session,
                resource_uri=env.environmentUri,
                group=data['SamlGroupName'],
                permissions=permissions.ENVIRONMENT_ALL,
                resource_type=Environment.__name__,
            )
            session.commit()

            activity = Activity(
                action='ENVIRONMENT:CREATE',
                label='ENVIRONMENT:CREATE',
                owner=context.username,
                summary=f'{context.username} linked environment {env.AwsAccountId} to organization {organization.name}',
                targetUri=env.environmentUri,
                targetType='env',
            )
            session.add(activity)

            return env

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.UPDATE_ENVIRONMENT)
    def update_environment(uri, data=None):

        context = get_context()

        EnvironmentService.check_environment(data)
        EnvironmentPermissionsValidationService.validate_group_membership(data.get('SamlGroupName'), context.groups,
                                                                          context.username)
        EnvironmentRequestValidationService.validate_resource_prefix(data)

        with context.db_engine.scoped_session() as session:

            environment = EnvironmentService._get_environment_by_uri(session, uri)
            previous_resource_prefix = environment.resourcePrefix

            if data.get('label'):
                environment.label = data.get('label')
            if data.get('description'):
                environment.description = data.get('description', 'No description provided')
            if data.get('tags'):
                environment.tags = data.get('tags')
            if data.get('resourcePrefix'):
                environment.resourcePrefix = data.get('resourcePrefix')

            EnvironmentService._update_env_parameters(session, environment, data)

            ResourcePolicy.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=environment.SamlGroupName,
                permissions=permissions.ENVIRONMENT_ALL,
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
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.INVITE_ENVIRONMENT_GROUP)
    def invite_group(uri, data=None) -> (Environment, EnvironmentGroup):
        EnvironmentRequestValidationService.validate_invite_params(data)

        group: str = data['groupUri']
        uri = data['environmentUri'],

        with get_context().db_engine.scoped_session() as session:
            EnvironmentPermissionsValidationService.validate_permissions(session, uri, data['permissions'], group)

            environment = EnvironmentService._get_environment_by_uri(session, uri)

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

            # If environment role is imported, then data.all should attach the policies at import time
            # If environment role is created in environment stack, then data.all should attach the policies in the env stack
            PolicyManager(
                role_name=env_group_iam_role_name,
                environmentUri=environment.environmentUri,
                account=environment.AwsAccountId,
                resource_prefix=environment.resourcePrefix,
            ).create_all_policies(managed=env_role_imported)

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
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                permissions=data['permissions'],
                resource_type=Environment.__name__,
            )

            return environment, environment_group

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.REMOVE_ENVIRONMENT_GROUP)
    def remove_group(uri, group):
        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService._get_environment_by_uri(session, uri)

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

            group_env_consumption_roles = EnvironmentRepository.query_user_environment_consumption_roles(
                session, [group], uri, {}
            ).all()
            if group_env_consumption_roles:
                raise exceptions.EnvironmentResourcesFound(
                    action='Remove Team',
                    message=f'Team: {group} has consumption role(s) on this environment.',
                )

            group_membership = EnvironmentService.find_environment_group(session, group, environment.environmentUri)

            PolicyManager(
                role_name=group_membership.environmentIAMRoleName,
                environmentUri=environment.environmentUri,
                account=environment.AwsAccountId,
                resource_prefix=environment.resourcePrefix,
            ).delete_all_policies()

            if group_membership:
                session.delete(group_membership)
                session.commit()

            ResourcePolicy.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                resource_type=Environment.__name__,
            )
            return environment

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.UPDATE_ENVIRONMENT_GROUP)
    def update_group_permissions(uri, data=None):
        EnvironmentRequestValidationService.validate_invite_params(data)

        group = data['groupUri']
        uri = data['environmentUri']

        with get_context().db_engine.scoped_session() as session:
            EnvironmentPermissionsValidationService.validate_permissions(session, uri, data['permissions'], group)

            environment = EnvironmentService._get_environment_by_uri(session, uri)

            group_membership = EnvironmentService.find_environment_group(session, group, environment.environmentUri)
            if not group_membership:
                raise exceptions.UnauthorizedOperation(
                    action='UPDATE_TEAM_ENVIRONMENT_PERMISSIONS',
                    message=f'Team {group.name} is not a member of the environment {environment.name}',
                )

            ResourcePolicy.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                resource_type=Environment.__name__,
            )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=environment.environmentUri,
                permissions=data['permissions'],
                resource_type=Environment.__name__,
            )
            return environment

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUP_PERMISSIONS)
    def list_group_permissions(uri, group_uri):
        # the permission checked
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentService.list_group_permissions_internal(session, uri, group_uri)

    @staticmethod
    def list_group_permissions_internal(session, uri, group_uri):
        """No permission check, only for internal usages"""
        environment = EnvironmentService._get_environment_by_uri(session, uri)

        return ResourcePolicy.get_resource_policy_permissions(
            session=session,
            group_uri=group_uri,
            resource_uri=environment.environmentUri,
        )

    @staticmethod
    def list_group_invitation_permissions():
        with get_context().db_engine.scoped_session() as session:
            group_invitation_permissions = []
            for p in permissions.ENVIRONMENT_INVITATION_REQUEST:
                group_invitation_permissions.append(
                    Permission.find_permission_by_name(
                        session=session,
                        permission_name=p,
                        permission_type=PermissionType.RESOURCE.name,
                    )
                )
            return group_invitation_permissions

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.ADD_ENVIRONMENT_CONSUMPTION_ROLES)
    def add_consumption_role(uri, data=None) -> (Environment, EnvironmentGroup):

        EnvironmentRequestValidationService.validate_add_consumption_role_params(data)
        with get_context().db_engine.scoped_session() as session:

            environment = EnvironmentService._get_environment_by_uri(session, data['environmentUri'])

            group: str = data['groupUri']
            IAMRoleArn: str = data['IAMRoleArn']

            role = IAM.get_role(environment.AwsAccountId, IAMRoleArn)
            if not role:
                raise exceptions.AWSResourceNotFound(
                    action='ADD_CONSUMPTION_ROLE',
                    message=f"{input['IAMRoleArn']} does not exist in this account",
                )

            alreadyAdded = EnvironmentRepository.find_consumption_roles_by_IAMArn(
                session, environment.environmentUri, IAMRoleArn
            )
            if alreadyAdded:
                raise exceptions.UnauthorizedOperation(
                    action='ADD_CONSUMPTION_ROLE',
                    message=f'IAM role {IAMRoleArn} is already added to the environment {environment.name}',
                )

            consumption_role = ConsumptionRole(
                consumptionRoleName=data['consumptionRoleName'],
                environmentUri=environment.environmentUri,
                groupUri=group,
                IAMRoleArn=IAMRoleArn,
                IAMRoleName=IAMRoleArn.split('/')[-1],
                dataallManaged=data['dataallManaged'],
            )

            PolicyManager(
                role_name=consumption_role.IAMRoleName,
                environmentUri=environment.environmentUri,
                account=environment.AwsAccountId,
                resource_prefix=environment.resourcePrefix,
            ).create_all_policies(managed=consumption_role.dataallManaged)

            session.add(consumption_role)
            session.commit()

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=consumption_role.consumptionRoleUri,
                permissions=permissions.CONSUMPTION_ROLE_ALL,
                resource_type=ConsumptionRole.__name__,
            )
            return consumption_role

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def remove_consumption_role(uri, env_uri):

        with get_context().db_engine.scoped_session() as session:
            consumption_role = EnvironmentRepository.get_environment_consumption_role(session, uri, env_uri)
            environment = EnvironmentService._get_environment_by_uri(session, env_uri)

            num_resources = EnvironmentResourceManager.count_consumption_role_resources(session, uri)
            if num_resources > 0:
                raise exceptions.EnvironmentResourcesFound(
                    action='Remove Consumption Role',
                    message=f'Consumption role: {consumption_role.consumptionRoleName} has created {num_resources} resources on this environment.',
                )

            if consumption_role:
                PolicyManager(
                    role_name=consumption_role.IAMRoleName,
                    environmentUri=environment.environmentUri,
                    account=environment.AwsAccountId,
                    resource_prefix=environment.resourcePrefix,
                ).delete_all_policies()

                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=consumption_role.groupUri,
                    resource_uri=consumption_role.consumptionRoleUri,
                    resource_type=ConsumptionRole.__name__,
                )

                session.delete(consumption_role)
                session.commit()

            return True

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def update_consumption_role(uri, env_uri, data):

        EnvironmentRequestValidationService.validate_update_consumption_role_params(data)
        with get_context().db_engine.scoped_session() as session:
            consumption_role = EnvironmentRepository.get_environment_consumption_role(session, uri, env_uri)
            if consumption_role:
                ResourcePolicy.update_resource_policy(
                    session=session,
                    resource_uri=uri,
                    resource_type=ConsumptionRole.__name__,
                    old_group=consumption_role.groupUri,
                    new_group=data['groupUri'],
                    new_permissions=permissions.CONSUMPTION_ROLE_ALL,
                )
                for key, value in data.items():
                    setattr(consumption_role, key, value)
                session.commit()
            return consumption_role

    @staticmethod
    def paginated_user_environments(data=None) -> dict:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environments(session, context.username, context.groups, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    def list_valid_user_environments(data=None) -> dict:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            query = EnvironmentRepository.query_user_environments(session, context.username, context.groups, data)

        valid_environments = []
        for env in query:
            stack = stack_helper.get_stack_with_cfn_resources(
                targetUri=env.environmentUri,
                environmentUri=env.environmentUri,
            )
            if stack.status in [
                StackStatus.CREATE_COMPLETE.value,
                StackStatus.UPDATE_COMPLETE.value,
                StackStatus.UPDATE_ROLLBACK_COMPLETE.value,
            ]:
                valid_environments.append(env)

        return {
            'count': len(valid_environments),
            'nodes': valid_environments,
        }

    @staticmethod
    def paginated_user_groups(data=None) -> dict:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_groups(session, context.username, context.groups, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    def paginated_user_consumption_roles(data=None) -> dict:
        context = get_context()
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_consumption_roles(session, context.username, context.groups,
                                                                         data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_user_environment_groups(uri, data=None) -> dict:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environment_groups(session, context.groups, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 1000),
            ).to_dict()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_all_environment_groups(uri, data=None) -> dict:
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_all_environment_groups(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def list_environment_groups(session, uri) -> [str]:
        return [
            g.groupUri
            for g in EnvironmentRepository.query_user_environment_groups(session, get_context().groups, uri, {}).all()
        ]

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_environment_invited_groups(uri, data=None) -> dict:
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_environment_invited_groups(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def list_environment_invited_groups(session, uri):
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentRepository.query_environment_invited_groups(session, uri, {}).all()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_user_environment_consumption_roles(uri, data=None) -> dict:
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_user_environment_consumption_roles(session, get_context().groups, uri,
                                                                                     data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 1000),
            ).to_dict()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_all_environment_consumption_roles(uri, data=None) -> dict:
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=EnvironmentRepository.query_all_environment_consumption_roles(session, uri, data),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def get_consumption_role(uri):
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentRepository.get_consumption_role(session, uri)

    @staticmethod
    def find_environment_group(session, group_uri, environment_uri):
        try:
            env_group = EnvironmentGroupRepository.get_environment_group(session, group_uri, environment_uri)
            return env_group
        except Exception:
            return None

    @staticmethod
    def get_environment_consumption_role(session, role_uri, environment_uri) -> ConsumptionRole:
        role = EnvironmentRepository.get_environment_consumption_role(session, role_uri, environment_uri)
        if not role:
            raise exceptions.ObjectNotFound('ConsumptionRoleUri', f'({role_uri},{environment_uri})')
        return role

    @staticmethod
    def _get_environment_by_uri(session, uri) -> Environment:
        return EnvironmentRepository.get_environment_by_uri(session, uri)

    @staticmethod
    def get_environment_by_uri(session=None, uri=None) -> Environment:
        if session:
            return EnvironmentService._get_environment_by_uri(session, uri)
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentService._get_environment_by_uri(session, uri)

    @staticmethod
    @has_resource_permission(permissions.GET_ENVIRONMENT)
    def check_permissions_and_get_environment_by_uri(uri) -> Environment:
        with get_context().db_engine.scoped_session() as session:
            return EnvironmentService._get_environment_by_uri(session, uri)

    @staticmethod
    def list_all_active_environments(session) -> [Environment]:
        """
        Lists all active dataall environments
        :param session:
        :return: [Environment]
        """
        environments: [Environment] = session.query(Environment).filter(Environment.deleted.is_(None)).all()
        log.info(f'Retrieved all active dataall environments {[e.AwsAccountId for e in environments]}')
        return environments

    @staticmethod
    @has_resource_permission(permissions.GET_ENVIRONMENT)
    def get_stack(session, uri, stack_uri) -> Stack:
        return session.query(Stack).get(stack_uri)

    @staticmethod
    @has_resource_permission(permissions.DELETE_ENVIRONMENT)
    def delete_environment(uri):
        with get_context().db_engine.scoped_session() as session:
            environment = EnvironmentService._get_environment_by_uri(session, uri)
            env_groups = session.query(EnvironmentGroup).filter(EnvironmentGroup.environmentUri == uri).all()
            env_roles = session.query(ConsumptionRole).filter(ConsumptionRole.environmentUri == uri).all()

            env_resources = 0
            for group in env_groups:
                env_resources += EnvironmentResourceManager.count_group_resources(session, environment, group.groupUri)
            for role in env_roles:
                env_resources += EnvironmentResourceManager.count_consumption_role_resources(
                    session, role.consumptionRoleUri
                )

            if env_resources > 0:
                raise exceptions.EnvironmentResourcesFound(
                    action='Delete Environment',
                    message=f'Found {env_resources} resources on environment {environment.label} - Delete all environment related objects before proceeding',
                )
            else:
                PolicyManager(
                    role_name=environment.EnvironmentDefaultIAMRoleName,
                    environmentUri=environment.environmentUri,
                    account=environment.AwsAccountId,
                    resource_prefix=environment.resourcePrefix,
                ).delete_all_policies()

                KeyValueTag.delete_key_value_tags(session, environment.environmentUri, 'environment')
                EnvironmentResourceManager.delete_env(session, environment)
                EnvironmentParameterRepository(session).delete_params(environment.environmentUri)

                for group in env_groups:
                    session.delete(group)

                    ResourcePolicy.delete_resource_policy(
                        session=session,
                        resource_uri=uri,
                        group=group.groupUri,
                    )

                for role in env_roles:
                    session.delete(role)

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
    def enable_subscriptions(environmentUri, username, groups, producersTopicArn):
        with get_context().db_engine.scoped_session() as session:
            ResourcePolicy.check_user_resource_permission(
                session=session,
                username=username,
                groups=groups,
                resource_uri=environmentUri,
                permission_name=permissions.ENABLE_ENVIRONMENT_SUBSCRIPTIONS,
            )
            environment = EnvironmentService._get_environment_by_uri(session, environmentUri)
            if producersTopicArn:
                environment.subscriptionsProducersTopicName = producersTopicArn
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

    @staticmethod
    def disable_subscriptions(environmentUri, username, groups):
        with get_context().db_engine.scoped_session() as session:
            ResourcePolicy.check_user_resource_permission(
                session=session,
                username=username,
                groups=groups,
                resource_uri=environmentUri,
                permission_name=permissions.ENABLE_ENVIRONMENT_SUBSCRIPTIONS,
            )
            environment = EnvironmentService._get_environment_by_uri(session, environmentUri)

            environment.subscriptionsConsumersTopicName = None
            environment.subscriptionsConsumersTopicImported = False
            environment.subscriptionsProducersTopicName = None
            environment.subscriptionsProducersTopicImported = False
            environment.subscriptionsEnabled = False
            session.commit()

    @staticmethod
    def resolve_user_role(owner, samlGroupName, environmentUri):
        context = get_context()
        if owner == context.username:
            return EnvironmentPermission.Owner.value
        elif samlGroupName in context.groups:
            return EnvironmentPermission.Admin.value
        else:
            with context.db_engine.scoped_session() as session:
                env_group = EnvironmentService.get_enviromment_groups_from_list(
                    session, environmentUri, context.groups
                )
                if env_group:
                    return EnvironmentPermission.Invited.value
            return EnvironmentPermission.NotInvited.value

    @staticmethod
    def _get_environment_group_aws_session(session, username, groups, environment, groupUri=None):
        if groupUri and groupUri not in groups:
            raise exceptions.UnauthorizedOperation(
                action='ENVIRONMENT_AWS_ACCESS',
                message=f'User: {username} is not member of the team {groupUri}',
            )
        pivot_session = SessionHelper.remote_session(environment.AwsAccountId)
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
            env_group = EnvironmentService._get_enviromment_group_by_uri(session, environment.environmentUri, groupUri)
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
    def get_environment_assume_role_url(environmentUri, groupUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
            return SessionHelper.get_console_access_url(
                EnvironmentService._get_environment_group_aws_session(
                    session=session,
                    username=context.username,
                    groups=context.groups,
                    environment=environment,
                    groupUri=groupUri,
                ),
                region=environment.region,
            )

    @staticmethod
    def generate_environment_access_token(environmentUri, groupUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
            c = EnvironmentService._get_environment_group_aws_session(
                session=session,
                username=context.username,
                groups=context.groups,
                environment=environment,
                groupUri=groupUri,
            ).get_credentials()
            credentials = {
                'AccessKey': c.access_key,
                'SessionKey': c.secret_key,
                'sessionToken': c.token,
            }
            return json.dumps(credentials)
