import logging
import re

from sqlalchemy import or_, case, func
from sqlalchemy.orm import Query
from sqlalchemy.sql import and_

from .. import exceptions, permissions, models, api
from . import (
    has_resource_perm,
    has_tenant_perm,
    ResourcePolicy,
    Permission,
    KeyValueTag
)
from ..api.organization import Organization
from ..models import EnvironmentGroup
from ..models.Enums import (
    ShareableType,
    EnvironmentType,
    EnvironmentPermission,
    PrincipalType

)
from ..models.Permission import PermissionType
from ..paginator import Page, paginate
from ...utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

log = logging.getLogger(__name__)


class Environment:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.LINK_ENVIRONMENT)
    def create_environment(session, username, groups, uri, data=None, check_perm=None):
        Environment._validate_creation_params(data, uri)
        organization = Organization.get_organization_by_uri(session, uri)
        env = models.Environment(
            organizationUri=data.get('organizationUri'),
            label=data.get('label', 'Unnamed'),
            tags=data.get('tags', []),
            owner=username,
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
            dashboardsEnabled=data.get('dashboardsEnabled', False),
            notebooksEnabled=data.get('notebooksEnabled', True),
            mlStudiosEnabled=data.get('mlStudiosEnabled', True),
            pipelinesEnabled=data.get('pipelinesEnabled', True),
            warehousesEnabled=data.get('warehousesEnabled', True),
            resourcePrefix=data.get('resourcePrefix'),
        )
        session.add(env)
        session.commit()

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
            vpc = models.Vpc(
                environmentUri=env.environmentUri,
                region=env.region,
                AwsAccountId=env.AwsAccountId,
                VpcId=data.get('vpcId'),
                privateSubnetIds=data.get('privateSubnetIds', []),
                publicSubnetIds=data.get('publicSubnetIds', []),
                SamlGroupName=data['SamlGroupName'],
                owner=username,
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
                resource_type=models.Vpc.__name__,
            )
        env_group = models.EnvironmentGroup(
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
            resource_type=models.Environment.__name__,
        )
        session.commit()

        activity = models.Activity(
            action='ENVIRONMENT:CREATE',
            label='ENVIRONMENT:CREATE',
            owner=username,
            summary=f'{username} linked environment {env.AwsAccountId} to organization {organization.name}',
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
        Environment._validate_resource_prefix(data)

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
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.UPDATE_ENVIRONMENT)
    def update_environment(session, username, groups, uri, data=None, check_perm=None):
        Environment._validate_resource_prefix(data)
        environment = Environment.get_environment_by_uri(session, uri)
        if data.get('label'):
            environment.label = data.get('label')
        if data.get('description'):
            environment.description = data.get('description', 'No description provided')
        if data.get('tags'):
            environment.tags = data.get('tags')
        if 'dashboardsEnabled' in data.keys():
            environment.dashboardsEnabled = data.get('dashboardsEnabled')
        if 'notebooksEnabled' in data.keys():
            environment.notebooksEnabled = data.get('notebooksEnabled')
        if 'mlStudiosEnabled' in data.keys():
            environment.mlStudiosEnabled = data.get('mlStudiosEnabled')
        if 'pipelinesEnabled' in data.keys():
            environment.pipelinesEnabled = data.get('pipelinesEnabled')
        if 'warehousesEnabled' in data.keys():
            environment.warehousesEnabled = data.get('warehousesEnabled')
        if data.get('resourcePrefix'):
            environment.resourcePrefix = data.get('resourcePrefix')

        ResourcePolicy.attach_resource_policy(
            session=session,
            resource_uri=environment.environmentUri,
            group=environment.SamlGroupName,
            permissions=permissions.ENVIRONMENT_ALL,
            resource_type=models.Environment.__name__,
        )
        return environment

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.INVITE_ENVIRONMENT_GROUP)
    def invite_group(
        session, username, groups, uri, data=None, check_perm=None
    ) -> (models.Environment, models.EnvironmentGroup):
        Environment.validate_invite_params(data)

        group: str = data['groupUri']

        Environment.validate_permissions(session, uri, data['permissions'], group)

        environment = Environment.get_environment_by_uri(session, uri)

        group_membership = Environment.find_environment_group(
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
            invitedBy=username,
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
            resource_type=models.Environment.__name__,
        )
        return environment, environment_group

    @staticmethod
    def validate_permissions(session, uri, g_permissions, group):

        if permissions.CREATE_DATASET in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_DATASETS)

        if permissions.CREATE_REDSHIFT_CLUSTER in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_REDSHIFT_CLUSTERS)

        if permissions.CREATE_NOTEBOOK in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_NOTEBOOKS)

        if permissions.CREATE_SGMSTUDIO_NOTEBOOK in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_SGMSTUDIO_NOTEBOOKS)

        if permissions.INVITE_ENVIRONMENT_GROUP in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_GROUPS)
            g_permissions.append(permissions.REMOVE_ENVIRONMENT_GROUP)

        if permissions.ADD_ENVIRONMENT_CONSUMPTION_ROLES in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)

        if permissions.CREATE_SHARE_OBJECT in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)

        if permissions.CREATE_NETWORK in g_permissions:
            g_permissions.append(permissions.LIST_ENVIRONMENT_NETWORKS)

        g_permissions.append(permissions.RUN_ATHENA_QUERY)
        g_permissions.append(permissions.GET_ENVIRONMENT)
        g_permissions.append(permissions.LIST_ENVIRONMENT_GROUPS)
        g_permissions.append(permissions.LIST_ENVIRONMENT_GROUP_PERMISSIONS)
        g_permissions.append(permissions.LIST_ENVIRONMENT_REDSHIFT_CLUSTERS)
        g_permissions.append(permissions.LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
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
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.REMOVE_ENVIRONMENT_GROUP)
    def remove_group(session, username, groups, uri, data=None, check_perm=None):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')

        group: str = data['groupUri']

        environment = Environment.get_environment_by_uri(session, uri)

        if group == environment.SamlGroupName:
            raise exceptions.UnauthorizedOperation(
                action='REMOVE_TEAM',
                message=f'Team: {group} is the owner of the environment {environment.name}',
            )

        group_env_objects_count = (
            session.query(models.Environment)
            .outerjoin(
                models.Dataset,
                models.Dataset.environmentUri == models.Environment.environmentUri,
            )
            .outerjoin(
                models.SagemakerStudioUserProfile,
                models.SagemakerStudioUserProfile.environmentUri
                == models.Environment.environmentUri,
            )
            .outerjoin(
                models.RedshiftCluster,
                models.RedshiftCluster.environmentUri
                == models.Environment.environmentUri,
            )
            .outerjoin(
                models.DataPipeline,
                models.DataPipeline.environmentUri == models.Environment.environmentUri,
            )
            .outerjoin(
                models.Dashboard,
                models.Dashboard.environmentUri == models.Environment.environmentUri,
            )
            .outerjoin(
                models.WorksheetQueryResult,
                models.WorksheetQueryResult.AwsAccountId
                == models.Environment.AwsAccountId,
            )
            .filter(
                and_(
                    models.Environment.environmentUri == environment.environmentUri,
                    or_(
                        models.RedshiftCluster.SamlGroupName == group,
                        models.Dataset.SamlAdminGroupName == group,
                        models.SagemakerStudioUserProfile.SamlAdminGroupName == group,
                        models.DataPipeline.SamlGroupName == group,
                        models.Dashboard.SamlGroupName == group,
                    ),
                )
            )
            .count()
        )

        if group_env_objects_count > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Remove Team',
                message=f'Team: {group} has created {group_env_objects_count} resources on this environment.',
            )

        shares_count = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.principalId == group,
                    models.ShareObject.principalType == PrincipalType.Group.value
                )
            )
            .count()
        )

        if shares_count > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Remove Team',
                message=f'Team: {group} has created {shares_count} share requests on this environment.',
            )

        group_membership = Environment.find_environment_group(
            session, group, environment.environmentUri
        )
        if group_membership:
            session.delete(group_membership)
            session.commit()

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=group,
            resource_uri=environment.environmentUri,
            resource_type=models.Environment.__name__,
        )
        return environment

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.UPDATE_ENVIRONMENT_GROUP)
    def update_group_permissions(
        session, username, groups, uri, data=None, check_perm=None
    ):
        Environment.validate_invite_params(data)

        group = data['groupUri']

        Environment.validate_permissions(session, uri, data['permissions'], group)

        environment = Environment.get_environment_by_uri(session, uri)

        group_membership = Environment.find_environment_group(
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
            resource_type=models.Environment.__name__,
        )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group,
            resource_uri=environment.environmentUri,
            permissions=data['permissions'],
            resource_type=models.Environment.__name__,
        )
        return environment

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUP_PERMISSIONS)
    def list_group_permissions(
        session, username, groups, uri, data=None, check_perm=None
    ):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')

        environment = Environment.get_environment_by_uri(session, uri)

        return ResourcePolicy.get_resource_policy_permissions(
            session=session,
            group_uri=data['groupUri'],
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
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.ADD_ENVIRONMENT_CONSUMPTION_ROLES)
    def add_consumption_role(
        session, username, groups, uri, data=None, check_perm=None
    ) -> (models.Environment, models.EnvironmentGroup):

        group: str = data['groupUri']
        IAMRoleArn: str = data['IAMRoleArn']
        environment = Environment.get_environment_by_uri(session, uri)

        alreadyAdded = Environment.find_consumption_roles_by_IAMArn(
            session, environment.environmentUri, IAMRoleArn
        )
        if alreadyAdded:
            raise exceptions.UnauthorizedOperation(
                action='ADD_CONSUMPTION_ROLE',
                message=f'IAM role {IAMRoleArn} is already added to the environment {environment.name}',
            )

        consumption_role = models.ConsumptionRole(
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
            resource_type=models.ConsumptionRole.__name__,
        )
        return consumption_role

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_perm(permissions.REMOVE_ENVIRONMENT_CONSUMPTION_ROLE)
    def remove_consumption_role(session, username, groups, uri, data=None, check_perm=None):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not uri:
            raise exceptions.RequiredParameter('consumptionRoleUri')

        consumption_role = Environment.get_environment_consumption_role(session, uri, data.get('environmentUri'))

        shares_count = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.principalId == uri,
                    models.ShareObject.principalType == PrincipalType.ConsumptionRole.value
                )
            )
            .count()
        )

        if shares_count > 0:
            raise exceptions.EnvironmentResourcesFound(
                action='Remove Consumption Role',
                message=f'Consumption role: {consumption_role.consumptionRoleName} has created {shares_count} share requests on this environment.',
            )

        if consumption_role:
            session.delete(consumption_role)
            session.commit()

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=consumption_role.groupUri,
            resource_uri=consumption_role.consumptionRoleUri,
            resource_type=models.ConsumptionRole.__name__,
        )
        return True

    @staticmethod
    def query_user_environments(session, username, groups, filter) -> Query:
        query = (
            session.query(models.Environment)
            .outerjoin(
                models.EnvironmentGroup,
                models.Environment.environmentUri
                == models.EnvironmentGroup.environmentUri,
            )
            .filter(
                or_(
                    models.Environment.owner == username,
                    models.EnvironmentGroup.groupUri.in_(groups),
                )
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.Environment.label.ilike('%' + term + '%'),
                    models.Environment.description.ilike('%' + term + '%'),
                    models.Environment.tags.contains(f'{{{term}}}'),
                    models.Environment.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_environments(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_user_environments(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 5),
        ).to_dict()

    @staticmethod
    def query_user_environment_groups(session, username, groups, uri, filter) -> Query:
        query = (
            session.query(models.EnvironmentGroup)
            .filter(models.EnvironmentGroup.environmentUri == uri)
            .filter(models.EnvironmentGroup.groupUri.in_(groups))
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_user_environment_groups(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_user_environment_groups(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    def query_all_environment_groups(session, uri, filter) -> Query:
        query = session.query(models.EnvironmentGroup).filter(
            models.EnvironmentGroup.environmentUri == uri
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_all_environment_groups(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_all_environment_groups(
                session, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUPS)
    def list_environment_groups(
        session, username, groups, uri, data=None, check_perm=None
    ) -> [str]:
        return [
            g.groupUri
            for g in Environment.query_user_environment_groups(
                session, username, groups, uri, data
            ).all()
        ]

    @staticmethod
    def query_environment_invited_groups(
        session, username, groups, uri, filter
    ) -> Query:
        query = (
            session.query(models.EnvironmentGroup)
            .join(
                models.Environment,
                models.EnvironmentGroup.environmentUri
                == models.Environment.environmentUri,
            )
            .filter(
                and_(
                    models.Environment.environmentUri == uri,
                    models.EnvironmentGroup.groupUri
                    != models.Environment.SamlGroupName,
                )
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.EnvironmentGroup.groupUri.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUPS)
    def paginated_environment_invited_groups(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_environment_invited_groups(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_GROUPS)
    def list_environment_invited_groups(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return Environment.query_environment_invited_groups(
            session, username, groups, uri, data
        ).all()

    @staticmethod
    def query_user_environment_consumption_roles(session, username, groups, uri, filter) -> Query:
        query = (
            session.query(models.ConsumptionRole)
            .filter(models.ConsumptionRole.environmentUri == uri)
            .filter(models.ConsumptionRole.groupUri.in_(groups))
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.ConsumptionRole.consumptionRoleName.ilike('%' + term + '%'),
                )
            )
        if filter and filter.get('groupUri'):
            print("filter group")
            group = filter['groupUri']
            query = query.filter(
                or_(
                    models.ConsumptionRole.groupUri == group,
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_user_environment_consumption_roles(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_user_environment_consumption_roles(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 1000),
        ).to_dict()

    @staticmethod
    def query_all_environment_consumption_roles(session, username, groups, uri, filter) -> Query:
        query = session.query(models.ConsumptionRole).filter(
            models.ConsumptionRole.environmentUri == uri
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.ConsumptionRole.consumptionRoleName.ilike('%' + term + '%'),
                )
            )
        if filter and filter.get('groupUri'):
            group = filter['groupUri']
            query = query.filter(
                or_(
                    models.ConsumptionRole.groupUri == group,
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def paginated_all_environment_consumption_roles(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_all_environment_consumption_roles(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_CONSUMPTION_ROLES)
    def list_environment_consumption_roles(
        session, username, groups, uri, data=None, check_perm=None
    ) -> [str]:
        return [
            {"value": g.IAMRoleArn, "label": g.consumptionRoleName}
            for g in Environment.query_user_environment_consumption_roles(
                session, username, groups, uri, data
            ).all()
        ]

    @staticmethod
    def find_consumption_roles_by_IAMArn(
            session, uri, arn
    ) -> Query:
        return session.query(models.ConsumptionRole).filter(
            and_(
                models.ConsumptionRole.environmentUri == uri,
                models.ConsumptionRole.IAMRoleArn == arn
            )
        ).first()

    @staticmethod
    def query_environment_datasets(session, username, groups, uri, filter) -> Query:
        query = session.query(models.Dataset).filter(
            and_(
                models.Dataset.environmentUri == uri,
                models.Dataset.deleted.is_(None),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.Dataset.label.ilike('%' + term + '%'),
                    models.Dataset.description.ilike('%' + term + '%'),
                    models.Dataset.tags.contains(f'{{{term}}}'),
                    models.Dataset.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def query_environment_group_datasets(session, username, groups, envUri, groupUri, filter) -> Query:
        query = session.query(models.Dataset).filter(
            and_(
                models.Dataset.environmentUri == envUri,
                models.Dataset.SamlAdminGroupName == groupUri,
                models.Dataset.deleted.is_(None),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    models.Dataset.label.ilike('%' + term + '%'),
                    models.Dataset.description.ilike('%' + term + '%'),
                    models.Dataset.tags.contains(f'{{{term}}}'),
                    models.Dataset.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_DATASETS)
    def paginated_environment_datasets(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_environment_datasets(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def paginated_environment_group_datasets(
        session, username, groups, envUri, groupUri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_environment_group_datasets(
                session, username, groups, envUri, groupUri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
    def paginated_shared_with_environment_datasets(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                models.ShareObjectItem.shareUri.label('shareUri'),
                models.Dataset.datasetUri.label('datasetUri'),
                models.Dataset.name.label('datasetName'),
                models.Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                models.ShareObject.created.label('created'),
                models.ShareObject.principalId.label('principalId'),
                models.ShareObject.principalType.label('principalType'),
                models.ShareObjectItem.itemType.label('itemType'),
                models.ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                models.ShareObjectItem.GlueTableName.label('GlueTableName'),
                models.ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                models.DatasetTable.GlueDatabaseName,
                                '.',
                                models.DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(models.DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.Dataset,
                models.ShareObject.datasetUri == models.Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == models.Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                models.DatasetTable,
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .outerjoin(
                models.DatasetStorageLocation,
                models.ShareObjectItem.itemUri
                == models.DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    models.ShareObject.environmentUri == uri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(models.ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[models.ShareObjectItem.itemType == t for t in itemTypes])
            )

        if data.get("uniqueShares", False):
            q = q.filter(models.ShareObject.principalType != PrincipalType.ConsumptionRole.value)
            q = q.distinct(models.ShareObject.shareUri)

        if data.get('term'):
            term = data.get('term')
            q = q.filter(models.ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def paginated_shared_with_environment_group_datasets(
        session, username, groups, envUri, groupUri, data=None, check_perm=None
    ) -> dict:
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                models.ShareObjectItem.shareUri.label('shareUri'),
                models.Dataset.datasetUri.label('datasetUri'),
                models.Dataset.name.label('datasetName'),
                models.Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                models.ShareObject.created.label('created'),
                models.ShareObject.principalId.label('principalId'),
                models.ShareObjectItem.itemType.label('itemType'),
                models.ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                models.ShareObjectItem.GlueTableName.label('GlueTableName'),
                models.ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                models.DatasetTable.GlueDatabaseName,
                                '.',
                                models.DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(models.DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.Dataset,
                models.ShareObject.datasetUri == models.Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == models.Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                models.DatasetTable,
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .outerjoin(
                models.DatasetStorageLocation,
                models.ShareObjectItem.itemUri
                == models.DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    models.ShareObject.environmentUri == envUri,
                    models.ShareObject.principalId == groupUri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(models.ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[models.ShareObjectItem.itemType == t for t in itemTypes])
            )
        if data.get('term'):
            term = data.get('term')
            q = q.filter(models.ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def query_environment_networks(session, username, groups, uri, filter) -> Query:
        query = session.query(models.Vpc).filter(
            models.Vpc.environmentUri == uri,
        )
        if filter.get('term'):
            term = filter.get('term')
            query = query.filter(
                or_(
                    models.Vpc.label.ilike('%' + term + '%'),
                    models.Vpc.VpcId.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_NETWORKS)
    def paginated_environment_networks(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Environment.query_environment_networks(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_DATASETS)
    def paginated_environment_data_items(
        session, username, groups, uri, data=None, check_perm=None
    ):
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                models.ShareObjectItem.shareUri.label('shareUri'),
                models.Dataset.datasetUri.label('datasetUri'),
                models.Dataset.name.label('datasetName'),
                models.Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                models.ShareObject.created.label('created'),
                models.ShareObjectItem.itemType.label('itemType'),
                models.ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                models.ShareObjectItem.GlueTableName.label('GlueTableName'),
                models.ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                models.DatasetTable.GlueDatabaseName,
                                '.',
                                models.DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(models.DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.Dataset,
                models.ShareObject.datasetUri == models.Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == models.Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                models.DatasetTable,
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .outerjoin(
                models.DatasetStorageLocation,
                models.ShareObjectItem.itemUri
                == models.DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    models.ShareObject.environmentUri == uri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(models.ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[models.ShareObjectItem.itemType == t for t in itemTypes])
            )
        if data.get('term'):
            term = data.get('term')
            q = q.filter(models.ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
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
            env_group = Environment.get_environment_group(session, group_uri, environment_uri)
            return env_group
        except Exception:
            return None

    @staticmethod
    def get_environment_group(session, group_uri, environment_uri):
        env_group = (
            session.query(models.EnvironmentGroup)
            .filter(
                (
                    and_(
                        models.EnvironmentGroup.groupUri == group_uri,
                        models.EnvironmentGroup.environmentUri == environment_uri,
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
            session.query(models.ConsumptionRole)
            .filter(
                (
                    and_(
                        models.ConsumptionRole.consumptionRoleUri == role_uri,
                        models.ConsumptionRole.environmentUri == environment_uri,
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
    def get_environment_by_uri(session, uri) -> models.Environment:
        if not uri:
            raise exceptions.RequiredParameter('environmentUri')
        environment: models.Environment = Environment.find_environment_by_uri(
            session, uri
        )
        if not environment:
            raise exceptions.ObjectNotFound(models.Environment.__name__, uri)
        return environment

    @staticmethod
    def find_environment_by_uri(session, uri) -> models.Environment:
        if not uri:
            raise exceptions.RequiredParameter('environmentUri')
        environment: models.Environment = session.query(models.Environment).get(uri)
        return environment

    @staticmethod
    def list_all_active_environments(session) -> [models.Environment]:
        """
        Lists all active dataall environments
        :param session:
        :return: [models.Environment]
        """
        environments: [models.Environment] = (
            session.query(models.Environment)
            .filter(models.Environment.deleted.is_(None))
            .all()
        )
        log.info(
            f'Retrieved all active dataall environments {[e.AwsAccountId for e in environments]}'
        )
        return environments

    @staticmethod
    def list_environment_redshift_clusters_query(session, environment_uri, filter):
        q = session.query(models.RedshiftCluster).filter(
            models.RedshiftCluster.environmentUri == environment_uri
        )
        term = filter.get('term', None)
        if term:
            q = q.filter(
                or_(
                    models.RedshiftCluster.label.ilike('%' + term + '%'),
                    models.RedshiftCluster.description.ilike('%' + term + '%'),
                )
            )
        return q

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_REDSHIFT_CLUSTERS)
    def paginated_environment_redshift_clusters(
        session, username, groups, uri, data=None, check_perm=None
    ):
        query = Environment.list_environment_redshift_clusters_query(session, uri, data)
        return paginate(
            query=query,
            page_size=data.get('pageSize', 10),
            page=data.get('page', 1),
        ).to_dict()

    @staticmethod
    def list_environment_objects(session, environment_uri):
        environment_objects = []
        datasets = (
            session.query(models.Dataset.label, models.Dataset.datasetUri)
            .filter(models.Dataset.environmentUri == environment_uri)
            .all()
        )
        notebooks = (
            session.query(
                models.SagemakerNotebook.label,
                models.SagemakerNotebook.notebookUri,
            )
            .filter(models.SagemakerNotebook.environmentUri == environment_uri)
            .all()
        )
        ml_studios = (
            session.query(
                models.SagemakerStudioUserProfile.label,
                models.SagemakerStudioUserProfile.sagemakerStudioUserProfileUri,
            )
            .filter(models.SagemakerStudioUserProfile.environmentUri == environment_uri)
            .all()
        )
        redshift_clusters = (
            session.query(
                models.RedshiftCluster.label, models.RedshiftCluster.clusterUri
            )
            .filter(models.RedshiftCluster.environmentUri == environment_uri)
            .all()
        )
        pipelines = (
            session.query(models.DataPipeline.label, models.DataPipeline.DataPipelineUri)
            .filter(models.DataPipeline.environmentUri == environment_uri)
            .all()
        )
        dashboards = (
            session.query(models.Dashboard.label, models.Dashboard.dashboardUri)
            .filter(models.Dashboard.environmentUri == environment_uri)
            .all()
        )
        if datasets:
            environment_objects.append({'type': 'Datasets', 'data': datasets})
        if notebooks:
            environment_objects.append({'type': 'Notebooks', 'data': notebooks})
        if ml_studios:
            environment_objects.append({'type': 'MLStudios', 'data': ml_studios})
        if redshift_clusters:
            environment_objects.append(
                {'type': 'RedshiftClusters', 'data': redshift_clusters}
            )
        if pipelines:
            environment_objects.append({'type': 'Pipelines', 'data': pipelines})
        if dashboards:
            environment_objects.append({'type': 'Dashboards', 'data': dashboards})
        return environment_objects

    @staticmethod
    def list_group_datasets(session, username, groups, uri, data=None, check_perm=None):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')

        return (
            session.query(models.Dataset)
            .filter(
                and_(
                    models.Dataset.environmentUri == uri,
                    models.Dataset.SamlAdminGroupName == data['groupUri'],
                )
            )
            .all()
        )

    @staticmethod
    @has_resource_perm(permissions.GET_ENVIRONMENT)
    def get_stack(
        session, username, groups, uri, data=None, check_perm=None
    ) -> models.Stack:
        return session.query(models.Stack).get(data['stackUri'])

    @staticmethod
    def delete_environment(session, username, groups, uri, data=None, check_perm=None):
        environment = data.get(
            'environment', Environment.get_environment_by_uri(session, uri)
        )

        environment_objects = Environment.list_environment_objects(session, uri)

        if environment_objects:
            raise exceptions.EnvironmentResourcesFound(
                action='Delete Environment',
                message='Delete all environment related objects before proceeding',
            )

        env_groups = (
            session.query(models.EnvironmentGroup)
            .filter(models.EnvironmentGroup.environmentUri == uri)
            .all()
        )
        for group in env_groups:

            session.delete(group)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=uri,
                group=group.groupUri,
            )

        env_roles = (
            session.query(models.ConsumptionRole)
            .filter(models.ConsumptionRole.environmentUri == uri)
            .all()
        )
        for role in env_roles:
            session.delete(role)

        KeyValueTag.delete_key_value_tags(
            session, environment.environmentUri, 'environment'
        )

        env_shared_with_objects = (
            session.query(models.ShareObject)
            .filter(models.ShareObject.environmentUri == environment.environmentUri)
            .all()
        )
        for share in env_shared_with_objects:
            (
                session.query(models.ShareObjectItem)
                .filter(models.ShareObjectItem.shareUri == share.shareUri)
                .delete()
            )
            session.delete(share)

        return session.delete(environment)

    @staticmethod
    def check_group_environment_membership(
        session, environment_uri, group, username, user_groups, permission_name
    ):
        if group and group not in user_groups:
            raise exceptions.UnauthorizedOperation(
                action=permission_name,
                message=f'User: {username} is not a member of the team {group}',
            )
        if group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=user_groups,
            uri=environment_uri,
            data={},
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permission_name,
                message=f'Team: {group} is not a member of the environment {environment_uri}',
            )

    @staticmethod
    def check_group_environment_permission(
        session, username, groups, uri, group, permission_name
    ):

        Environment.check_group_environment_membership(
            session=session,
            username=username,
            user_groups=groups,
            group=group,
            environment_uri=uri,
            permission_name=permission_name,
        )

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=[group],
            resource_uri=uri,
            permission_name=permission_name,
        )
