import logging
import re

from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.sql import and_

from dataall.base.context import get_context
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentParameter, ConsumptionRole
from dataall.core.environment.db.environment_repositories import EnvironmentParameterRepository, EnvironmentRepository
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.core.permissions.db.permission_repositories import Permission
from dataall.core.permissions.db.permission_models import PermissionType
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.vpc.db.vpc_models import Vpc
from dataall.base.db.paginator import paginate
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.db import exceptions
from dataall.core.permissions import permissions
from dataall.core.organizations.db.organization_repositories import Organization
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.api.enums import EnvironmentPermission, EnvironmentType

from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_models import Stack

log = logging.getLogger(__name__)


class EnvironmentService:

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.LINK_ENVIRONMENT)
    def create_environment(session, uri, data=None):
        context = get_context()
        EnvironmentService._validate_creation_params(data, uri)
        organization = Organization.get_organization_by_uri(session, uri)
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
            userRoleInEnvironment=EnvironmentPermission.Owner.value,
            EnvironmentDefaultIAMRoleName=data.get(
                'EnvironmentDefaultIAMRoleName', 'unknown'
            ),
            EnvironmentDefaultIAMRoleArn=f'arn:aws:iam::{data.get("AwsAccountId")}:role/{data.get("EnvironmentDefaultIAMRoleName")}',
            CDKRoleArn=f"arn:aws:iam::{data.get('AwsAccountId')}:role/{data['cdk_role_name']}",
            resourcePrefix=data.get('resourcePrefix'),
        )

        session.add(env)
        session.commit()

        EnvironmentService._update_env_parameters(session, env, data)

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

        if not data.get('EnvironmentDefaultIAMRoleName'):
            env_role_name = NamingConventionService(
                target_uri=env.environmentUri,
                target_label=env.label,
                pattern=NamingConventionPattern.IAM,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()
            env.EnvironmentDefaultIAMRoleName = env_role_name
            env.EnvironmentDefaultIAMRoleArn = (
                f'arn:aws:iam::{env.AwsAccountId}:role/{env_role_name}'
            )
            env.EnvironmentDefaultIAMRoleImported = False
        else:
            env.EnvironmentDefaultIAMRoleName = data['EnvironmentDefaultIAMRoleName']
            env.EnvironmentDefaultIAMRoleArn = f'arn:aws:iam::{env.AwsAccountId}:role/{env.EnvironmentDefaultIAMRoleName}'
            env.EnvironmentDefaultIAMRoleImported = True

        if data.get('vpcId'):
            vpc = Vpc(
                environmentUri=env.environmentUri,
                region=env.region,
                AwsAccountId=env.AwsAccountId,
                VpcId=data.get('vpcId'),
                privateSubnetIds=data.get('privateSubnetIds', []),
                publicSubnetIds=data.get('publicSubnetIds', []),
                SamlGroupName=data['SamlGroupName'],
                owner=context.username,
                label=f"{env.name}-{data.get('vpcId')}",
                name=f"{env.name}-{data.get('vpcId')}",
                default=True,
            )
            session.add(vpc)
            session.commit()
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=data['SamlGroupName'],
                permissions=permissions.NETWORK_ALL,
                resource_uri=vpc.vpcUri,
                resource_type=Vpc.__name__,
            )
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
    def _validate_creation_params(data, uri):
        if not uri:
            raise exceptions.RequiredParameter('organizationUri')
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('group')
        EnvironmentService._validate_resource_prefix(data)

    @staticmethod
    def _validate_resource_prefix(data):
        if data.get('resourcePrefix') and not bool(
            re.match(r'^[a-z-]+$', data.get('resourcePrefix'))
        ):
            raise exceptions.InvalidInput(
                'resourcePrefix',
                data.get('resourcePrefix'),
                'must match the pattern ^[a-z-]+$',
            )

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.UPDATE_ENVIRONMENT)
    def update_environment(session, uri, data=None):
        EnvironmentService._validate_resource_prefix(data)
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

        ResourcePolicy.attach_resource_policy(
            session=session,
            resource_uri=environment.environmentUri,
            group=environment.SamlGroupName,
            permissions=permissions.ENVIRONMENT_ALL,
            resource_type=Environment.__name__,
        )
        return environment

    @staticmethod
    def _update_env_parameters(session, env: Environment, data):
        """Removes old parameters and creates new parameters associated with the environment"""
        params = data.get("parameters")
        if not params:
            return

        env_uri = env.environmentUri
        new_params = [
            EnvironmentParameter(env_uri, param.get("key"), param.get("value"))
            for param in params
        ]
        EnvironmentParameterRepository(session).update_params(env_uri, new_params)

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.INVITE_ENVIRONMENT_GROUP)
    def invite_group(session, uri, data=None) -> (Environment, EnvironmentGroup):
        EnvironmentService.validate_invite_params(data)

        group: str = data['groupUri']

        EnvironmentService.validate_permissions(session, uri, data['permissions'], group)

        environment = EnvironmentService.get_environment_by_uri(session, uri)

        group_membership = EnvironmentService.find_environment_group(
            session, group, environment.environmentUri
        )
        if group_membership:
            raise exceptions.UnauthorizedOperation(
                action='INVITE_TEAM',
                message=f'Team {group} is already a member of the environment {environment.name}',
            )

        if data.get('environmentIAMRoleName'):
            env_group_iam_role_name = data['environmentIAMRoleName']
            env_role_imported = True
        else:
            env_group_iam_role_name = NamingConventionService(
                target_uri=environment.environmentUri,
                target_label=group,
                pattern=NamingConventionPattern.IAM,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name()
            env_role_imported = False

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
            environmentIAMRoleArn=f'arn:aws:iam::{environment.AwsAccountId}:role/{env_group_iam_role_name}',
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
    def validate_permissions(session, uri, g_permissions, group):
        if permissions.INVITE_ENVIRONMENT_GROUP in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_GROUPS)
            g_permissions.append(permissions.REMOVE_ENVIRONMENT_GROUP)

        if permissions.ADD_ENVIRONMENT_CONSUMPTION_ROLES in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)

        if permissions.CREATE_NETWORK in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_NETWORKS)

        g_permissions.append(permissions.GET_ENVIRONMENT)
        g_permissions.append(permissions.LIST_ENVIRONMENT_GROUPS)
        g_permissions.append(permissions.LIST_ENVIRONMENT_GROUP_PERMISSIONS)
        g_permissions.append(permissions.LIST_ENVIRONMENT_NETWORKS)
        g_permissions.append(permissions.CREDENTIALS_ENVIRONMENT)

        g_permissions = list(set(g_permissions))

        if g_permissions not in permissions.ENVIRONMENT_INVITED:
            exceptions.PermissionUnauthorized(
                action='INVITE_TEAM', group_name=group, resource_uri=uri
            )

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
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.REMOVE_ENVIRONMENT_GROUP)
    def remove_group(session, uri, group):
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        if group == environment.SamlGroupName:
            raise exceptions.UnauthorizedOperation(
                action='REMOVE_TEAM',
                message=f'Team: {group} is the owner of the environment {environment.name}',
            )

        group_env_objects_count = EnvironmentResourceManager.count_group_resources(
            session=session,
            environment=environment,
            group_uri=group
        )

        if group_env_objects_count > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Remove Team',
                message=f'Team: {group} has created {group_env_objects_count} resources on this environment.',
            )

        group_membership = EnvironmentService.find_environment_group(
            session, group, environment.environmentUri
        )
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
    def update_group_permissions(session, uri, data=None):
        EnvironmentService.validate_invite_params(data)

        group = data['groupUri']

        EnvironmentService.validate_permissions(session, uri, data['permissions'], group)

        environment = EnvironmentService.get_environment_by_uri(session, uri)

        group_membership = EnvironmentService.find_environment_group(
            session, group, environment.environmentUri
        )
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
    def list_group_permissions(session, uri, group_uri):
        # the permission checked
        return EnvironmentService.list_group_permissions_internal(session, uri, group_uri)

    @staticmethod
    def list_group_permissions_internal(session, uri, group_uri):
        """No permission check, only for internal usages"""
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        return ResourcePolicy.get_resource_policy_permissions(
            session=session,
            group_uri=group_uri,
            resource_uri=environment.environmentUri,
        )

    @staticmethod
    def list_group_invitation_permissions(
        session, username, groups, uri, data=None, check_perm=None
    ):
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
    def add_consumption_role(session, uri, data=None) -> (Environment, EnvironmentGroup):

        group: str = data['groupUri']
        IAMRoleArn: str = data['IAMRoleArn']
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        alreadyAdded = EnvironmentService.find_consumption_roles_by_IAMArn(
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
            IAMRoleName=IAMRoleArn.split("/")[-1],
        )

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
    def remove_consumption_role(session, uri, env_uri):
        consumption_role = EnvironmentService.get_environment_consumption_role(session, uri, env_uri)

        num_resources = EnvironmentResourceManager.count_consumption_role_resources(session, uri)
        if num_resources > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Remove Consumption Role',
                message=f'Consumption role: {consumption_role.consumptionRoleName} has created {num_resources} resources on this environment.',
            )

        if consumption_role:
            session.delete(consumption_role)
            session.commit()

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=consumption_role.groupUri,
            resource_uri=consumption_role.consumptionRoleUri,
            resource_type=ConsumptionRole.__name__,
        )
        return True

    @staticmethod
    def query_user_environments(session, username, groups, filter) -> Query:
        query = (
            session.query(Environment)
            .outerjoin(
                EnvironmentGroup,
                Environment.environmentUri
                == EnvironmentGroup.environmentUri,
            )
            .filter(
                or_(
                    Environment.owner == username,
                    EnvironmentGroup.groupUri.in_(groups),
                )
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    Environment.label.ilike('%' + term + '%'),
                    Environment.description.ilike('%' + term + '%'),
                    Environment.tags.contains(f'{{{term}}}'),
                    Environment.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_environments(session, data=None) -> dict:
        context = get_context()
        return paginate(
            query=EnvironmentService.query_user_environments(session, context.username, context.groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 5),
        ).to_dict()

    @staticmethod
    def query_user_environment_groups(session, groups, uri, filter) -> Query:
        query = (
            session.query(EnvironmentGroup)
            .filter(EnvironmentGroup.environmentUri == uri)
            .filter(EnvironmentGroup.groupUri.in_(groups))
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_user_environment_groups(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentService.query_user_environment_groups(
                session, get_context().groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    def query_all_environment_groups(session, uri, filter) -> Query:
        query = session.query(EnvironmentGroup).filter(
            EnvironmentGroup.environmentUri == uri
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_all_environment_groups(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentService.query_all_environment_groups(
                session, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def list_environment_groups(session, uri) -> [str]:
        return [
            g.groupUri
            for g in EnvironmentService.query_user_environment_groups(
                session, get_context().groups, uri, {}
            ).all()
        ]

    @staticmethod
    def query_environment_invited_groups(session, uri, filter) -> Query:
        query = (
            session.query(EnvironmentGroup)
            .join(
                Environment,
                EnvironmentGroup.environmentUri
                == Environment.environmentUri,
            )
            .filter(
                and_(
                    Environment.environmentUri == uri,
                    EnvironmentGroup.groupUri
                    != Environment.SamlGroupName,
                )
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_environment_invited_groups(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentService.query_environment_invited_groups(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def list_environment_invited_groups(session, uri):
        return EnvironmentService.query_environment_invited_groups(session, uri, {}).all()

    @staticmethod
    def query_user_environment_consumption_roles(session, groups, uri, filter) -> Query:
        query = (
            session.query(ConsumptionRole)
            .filter(ConsumptionRole.environmentUri == uri)
            .filter(ConsumptionRole.groupUri.in_(groups))
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    ConsumptionRole.consumptionRoleName.ilike('%' + term + '%'),
                )
            )
        if filter and filter.get('groupUri'):
            print("filter group")
            group = filter['groupUri']
            query = query.filter(
                or_(
                    ConsumptionRole.groupUri == group,
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_user_environment_consumption_roles(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentService.query_user_environment_consumption_roles(
                session, get_context().groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    def query_all_environment_consumption_roles(session, uri, filter) -> Query:
        query = session.query(ConsumptionRole).filter(
            ConsumptionRole.environmentUri == uri
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    ConsumptionRole.consumptionRoleName.ilike('%' + term + '%'),
                )
            )
        if filter and filter.get('groupUri'):
            group = filter['groupUri']
            query = query.filter(
                or_(
                    ConsumptionRole.groupUri == group,
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_all_environment_consumption_roles(
        session, uri, data=None
    ) -> dict:
        return paginate(
            query=EnvironmentService.query_all_environment_consumption_roles(
                session, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def find_consumption_roles_by_IAMArn(session, uri, arn) -> Query:
        return session.query(ConsumptionRole).filter(
            and_(
                ConsumptionRole.environmentUri == uri,
                ConsumptionRole.IAMRoleArn == arn
            )
        ).first()

    @staticmethod
    def query_environment_networks(session, uri, filter) -> Query:
        query = session.query(Vpc).filter(
            Vpc.environmentUri == uri,
        )
        if filter.get('term'):
            term = filter.get('term')
            query = query.filter(
                or_(
                    Vpc.label.ilike('%' + term + '%'),
                    Vpc.VpcId.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_permission(permissions.LIST_ENVIRONMENT_NETWORKS)
    def paginated_environment_networks(session, uri, data=None) -> dict:
        return paginate(
            query=EnvironmentService.query_environment_networks(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def validate_invite_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')

    @staticmethod
    def find_environment_group(session, group_uri, environment_uri):
        try:
            env_group = EnvironmentService.get_environment_group(session, group_uri, environment_uri)
            return env_group
        except Exception:
            return None

    @staticmethod
    def get_environment_group(session, group_uri, environment_uri):
        env_group = (
            session.query(EnvironmentGroup)
            .filter(
                (
                    and_(
                        EnvironmentGroup.groupUri == group_uri,
                        EnvironmentGroup.environmentUri == environment_uri,
                    )
                )
            )
            .first()
        )
        if not env_group:
            raise exceptions.ObjectNotFound(
                'EnvironmentGroup', f'({group_uri},{environment_uri})'
            )
        return env_group

    @staticmethod
    def get_environment_consumption_role(session, role_uri, environment_uri):
        role = (
            session.query(ConsumptionRole)
            .filter(
                (
                    and_(
                        ConsumptionRole.consumptionRoleUri == role_uri,
                        ConsumptionRole.environmentUri == environment_uri,
                    )
                )
            )
            .first()
        )
        if not role:
            raise exceptions.ObjectNotFound(
                'ConsumptionRoleUri', f'({role_uri},{environment_uri})'
            )
        return role

    @staticmethod
    def get_environment_by_uri(session, uri) -> Environment:
        return EnvironmentRepository.get_environment_by_uri(session, uri)

    @staticmethod
    @has_resource_permission(permissions.GET_ENVIRONMENT)
    def find_environment_by_uri(session, uri) -> Environment:
        return EnvironmentService.get_environment_by_uri(session, uri)

    @staticmethod
    def list_all_active_environments(session) -> [Environment]:
        """
        Lists all active dataall environments
        :param session:
        :return: [Environment]
        """
        environments: [Environment] = (
            session.query(Environment)
            .filter(Environment.deleted.is_(None))
            .all()
        )
        log.info(
            f'Retrieved all active dataall environments {[e.AwsAccountId for e in environments]}'
        )
        return environments

    @staticmethod
    @has_resource_permission(permissions.GET_ENVIRONMENT)
    def get_stack(session, uri, stack_uri) -> Stack:
        return session.query(Stack).get(stack_uri)

    @staticmethod
    @has_resource_permission(permissions.DELETE_ENVIRONMENT)
    def delete_environment(session, uri, environment):
        env_groups = (
            session.query(EnvironmentGroup)
            .filter(EnvironmentGroup.environmentUri == uri)
            .all()
        )
        env_roles = (
            session.query(ConsumptionRole)
            .filter(ConsumptionRole.environmentUri == uri)
            .all()
        )

        env_resources = 0
        for group in env_groups:
            env_resources += EnvironmentResourceManager.count_group_resources(
                session,
                environment,
                group.groupUri
            )
        for role in env_roles:
            env_resources += EnvironmentResourceManager.count_consumption_role_resources(
                session,
                role.consumptionRoleUri
            )

        if env_resources > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Delete Environment',
                message=f'Found {env_resources} resources on environment {environment.label} - Delete all environment related objects before proceeding',
            )
        else:
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

            KeyValueTag.delete_key_value_tags(
                session, environment.environmentUri, 'environment'
            )

            return session.delete(environment)

    @staticmethod
    def get_environment_parameters(session, env_uri):
        return EnvironmentParameterRepository(session).get_params(env_uri)

    @staticmethod
    def get_boolean_env_param(session, env: Environment, param: str) -> bool:
        param = EnvironmentParameterRepository(session).get_param(env.environmentUri, param)
        return param is not None and param.value.lower() == "true"
