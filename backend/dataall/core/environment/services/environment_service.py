import logging
import re

from sqlalchemy.orm import Query

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentParameter, ConsumptionRole
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
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.api.enums import EnvironmentPermission, EnvironmentType

from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_models import Stack
from dataall.core.stacks.api.enums import StackStatus
from dataall.core.environment.services.managed_iam_policies import PolicyManager

from dataall.core.permissions.services.organization_permissions import LINK_ENVIRONMENT
from dataall.core.permissions.services import environment_permissions
from dataall.core.permissions.services.tenant_permissions import MANAGE_ENVIRONMENTS
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.vpc.db.vpc_repositories import VpcRepository

log = logging.getLogger(__name__)


class EnvironmentRequestValidationService:
    @staticmethod
    def validate_update_consumption_role(data):
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

    @staticmethod
    def validate_creation_params(data, uri, session):
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
                f"{data.get('AwsAccountId')}/{data.get('region')}",
                f"unique. An environment for {data.get('AwsAccountId')}/{data.get('region')} already exists",
            )


class EnvironmentService:
    @staticmethod
    def validate_permissions(session, uri, g_permissions, group):
        """
        g_permissions: coming from frontend = ENVIRONMENT_INVITATION_REQUEST

        """
        if environment_permissions.INVITE_ENVIRONMENT_GROUP in g_permissions:
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
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(LINK_ENVIRONMENT)
    def create_environment(session, uri, data=None):
        context = get_context()
        EnvironmentRequestValidationService.validate_creation_params(data, uri, session)
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
            CDKRoleArn=f"arn:aws:iam::{data.get('AwsAccountId')}:role/{data['cdk_role_name']}",
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
            summary=f'{context.username} linked environment {env.AwsAccountId} to organization {organization.name}',
            targetUri=env.environmentUri,
            targetType='env',
        )
        session.add(activity)
        return env

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.UPDATE_ENVIRONMENT)
    def update_environment(session, uri, data=None):
        EnvironmentRequestValidationService.validate_resource_prefix(data)
        environment = EnvironmentService.get_environment_by_uri(session, uri)
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
        return environment

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
    def invite_group(session, uri, data=None) -> (Environment, EnvironmentGroup):
        EnvironmentRequestValidationService.validate_invite_params(data)

        group: str = data['groupUri']

        EnvironmentService.validate_permissions(session, uri, data['permissions'], group)

        environment = EnvironmentService.get_environment_by_uri(session, uri)

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
            region=environment.region,
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
    def remove_group(session, uri, group):
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
            region=environment.region,
            resource_prefix=environment.resourcePrefix,
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
    def update_group_permissions(session, uri, data=None):
        EnvironmentRequestValidationService.validate_invite_params(data)

        group = data['groupUri']

        EnvironmentService.validate_permissions(session, uri, data['permissions'], group)

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
    def list_group_permissions(session, uri, group_uri):
        # the permission checked
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
    def list_group_invitation_permissions(session, username, groups, uri, data=None, check_perm=None):
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
    def add_consumption_role(session, uri, data=None) -> (Environment, EnvironmentGroup):
        group: str = data['groupUri']
        IAMRoleArn: str = data['IAMRoleArn']
        environment = EnvironmentService.get_environment_by_uri(session, uri)

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
            region=environment.region,
            resource_prefix=environment.resourcePrefix,
        ).create_all_policies(managed=consumption_role.dataallManaged)

        session.add(consumption_role)
        session.commit()

        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group,
            resource_uri=consumption_role.consumptionRoleUri,
            permissions=environment_permissions.CONSUMPTION_ROLE_ALL,
            resource_type=ConsumptionRole.__name__,
        )
        return consumption_role

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def remove_consumption_role(session, uri, env_uri):
        consumption_role = EnvironmentService.get_environment_consumption_role(session, uri, env_uri)
        environment = EnvironmentService.get_environment_by_uri(session, env_uri)

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
                region=environment.region,
                resource_prefix=environment.resourcePrefix,
            ).delete_all_policies()

            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=consumption_role.groupUri,
                resource_uri=consumption_role.consumptionRoleUri,
                resource_type=ConsumptionRole.__name__,
            )

            session.delete(consumption_role)
            session.commit()

        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(environment_permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def update_consumption_role(session, uri, env_uri, input):
        EnvironmentRequestValidationService.validate_update_consumption_role(input)
        consumption_role = EnvironmentService.get_environment_consumption_role(session, uri, env_uri)
        if consumption_role:
            ResourcePolicyService.update_resource_policy(
                session=session,
                resource_uri=uri,
                resource_type=ConsumptionRole.__name__,
                old_group=consumption_role.groupUri,
                new_group=input['groupUri'],
                new_permissions=environment_permissions.CONSUMPTION_ROLE_ALL,
            )
            for key, value in input.items():
                setattr(consumption_role, key, value)
            session.commit()
        return consumption_role

    @staticmethod
    def paginated_user_environments(session, data=None) -> dict:
        context = get_context()
        return paginate(
            query=EnvironmentRepository.query_user_environments(session, context.username, context.groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 5),
        ).to_dict()

    @staticmethod
    def list_valid_user_environments(session, data=None) -> dict:
        context = get_context()
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
    def paginated_user_groups(session, data=None) -> dict:
        context = get_context()
        return paginate(
            query=EnvironmentRepository.query_user_groups(session, context.username, context.groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 5),
        ).to_dict()

    @staticmethod
    def paginated_user_consumption_roles(session, data=None) -> dict:
        context = get_context()
        return paginate(
            query=EnvironmentRepository.query_user_consumption_roles(session, context.username, context.groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 5),
        ).to_dict()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_user_environment_groups(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentRepository.query_user_environment_groups(session, get_context().groups, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    def get_all_environment_groups(session, uri, filter) -> Query:
        return EnvironmentRepository.query_all_environment_groups(session, uri, filter)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_all_environment_groups(session, uri, data=None) -> dict:
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
    def paginated_environment_invited_groups(session, uri, data=None) -> dict:
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
    def paginated_user_environment_consumption_roles(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentRepository.query_user_environment_consumption_roles(
                session, get_context().groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_all_environment_consumption_roles(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentRepository.query_all_environment_consumption_roles(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def get_consumption_role(session, uri) -> Query:
        return EnvironmentRepository.get_consumption_role(session, uri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.LIST_ENVIRONMENT_NETWORKS)
    def paginated_environment_networks(session, uri, data=None) -> dict:
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
    def get_environment_group(session, group_uri, environment_uri):
        env_group = EnvironmentRepository.get_environment_group(session, group_uri, environment_uri)
        if not env_group:
            raise exceptions.ObjectNotFound('EnvironmentGroup', f'({group_uri},{environment_uri})')
        return env_group

    @staticmethod
    def get_environment_consumption_role(session, role_uri, environment_uri) -> ConsumptionRole:
        role = EnvironmentRepository.get_environment_consumption_role(session, role_uri, environment_uri)
        if not role:
            raise exceptions.ObjectNotFound('ConsumptionRoleUri', f'({role_uri},{environment_uri})')
        return role

    @staticmethod
    def get_environment_by_uri(session, uri) -> Environment:
        return EnvironmentRepository.get_environment_by_uri(session, uri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(environment_permissions.GET_ENVIRONMENT)
    def find_environment_by_uri(session, uri) -> Environment:
        return EnvironmentService.get_environment_by_uri(session, uri)

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
    @ResourcePolicyService.has_resource_permission(environment_permissions.DELETE_ENVIRONMENT)
    def delete_environment(session, uri, environment):
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
                message=f'Found {env_resources} resources on environment {environment.label} - Delete all environment '
                        f'related objects before proceeding',
            )
        else:
            PolicyManager(
                role_name=environment.EnvironmentDefaultIAMRoleName,
                environmentUri=environment.environmentUri,
                account=environment.AwsAccountId,
                region=environment.region,
                resource_prefix=environment.resourcePrefix,
            ).delete_all_policies()

            KeyValueTag.delete_key_value_tags(session, environment.environmentUri, 'environment')
            EnvironmentResourceManager.delete_env(session, environment)
            EnvironmentParameterRepository(session).delete_params(environment.environmentUri)

            for group in env_groups:
                session.delete(group)

                ResourcePolicyService.delete_resource_policy(
                    session=session,
                    resource_uri=uri,
                    group=group.groupUri,
                )

            for role in env_roles:
                session.delete(role)

            return session.delete(environment)

    @staticmethod
    def get_environment_parameters(session, env_uri):
        return EnvironmentParameterRepository(session).get_params(env_uri)

    @staticmethod
    def get_boolean_env_param(session, env: Environment, param: str) -> bool:
        param = EnvironmentParameterRepository(session).get_param(env.environmentUri, param)
        return param is not None and param.value.lower() == 'true'

    @staticmethod
    def is_user_invited(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return EnvironmentRepository.is_user_invited_to_environment(session=session, groups=context.groups, uri=uri)
