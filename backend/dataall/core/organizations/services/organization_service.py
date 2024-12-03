from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.organizations.services.organizations_enums import OrganisationUserRole
from dataall.core.organizations.db.organization_models import OrganizationGroup
from dataall.core.organizations.db import organization_models as models
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.tenant_permissions import MANAGE_ORGANIZATIONS
from dataall.core.permissions.services.organization_permissions import (
    ORGANIZATION_ALL,
    UPDATE_ORGANIZATION,
    GET_ORGANIZATION,
    INVITE_ORGANIZATION_GROUP,
    REMOVE_ORGANIZATION_GROUP,
    DELETE_ORGANIZATION,
    ORGANIZATION_INVITED_READONLY,
    ORGANIZATION_INVITED_DESCRIPTIONS,
)


class OrganizationService:
    """Service that serves request related to organization"""

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    def create_organization(data):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            username = context.username
            org = models.Organization(
                label=data.get('label'),
                owner=username,
                tags=data.get('tags', []),
                description=data.get('description', 'No description provided'),
                SamlGroupName=data.get('SamlGroupName'),
                userRoleInOrganization=OrganisationUserRole.Owner.value,
            )
            session.add(org)
            session.commit()

            member = models.OrganizationGroup(
                organizationUri=org.organizationUri,
                groupUri=data['SamlGroupName'],
            )
            session.add(member)

            activity = Activity(
                action='org:create',
                label='org:create',
                owner=username,
                summary=f'{username} create organization {org.name} ',
                targetUri=org.organizationUri,
                targetType='org',
            )
            session.add(activity)

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=data['SamlGroupName'],
                permissions=ORGANIZATION_ALL,
                resource_uri=org.organizationUri,
                resource_type=models.Organization.__name__,
            )

            return org

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    @ResourcePolicyService.has_resource_permission(UPDATE_ORGANIZATION)
    def update_organization(uri, data):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            organization = OrganizationRepository.get_organization_by_uri(session, uri)
            for field in data.keys():
                setattr(organization, field, data.get(field))
            session.commit()

            activity = Activity(
                action='org:update',
                label='org:create',
                owner=context.username,
                summary=f'{context.username} updated organization {organization.name} ',
                targetUri=organization.organizationUri,
                targetType='org',
            )
            session.add(activity)
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=organization.SamlGroupName,
                permissions=ORGANIZATION_ALL,
                resource_uri=organization.organizationUri,
                resource_type=models.Organization.__name__,
            )
            return organization

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_ORGANIZATION)
    def get_organization(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return OrganizationRepository.get_organization_by_uri(session=session, uri=uri)

    @staticmethod
    def get_organization_simplified(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return OrganizationRepository.get_organization_by_uri(session=session, uri=uri)

    @staticmethod
    def list_organizations(filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return OrganizationRepository.paginated_user_organizations(
                session=session,
                data=filter,
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_ORGANIZATION)
    def list_organization_environments(filter, uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return OrganizationRepository.paginated_organization_environments(
                session=session,
                uri=uri,
                data=filter,
            )

    @staticmethod
    def count_organization_resources(uri, group):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environments = EnvironmentRepository.count_environments_with_organization_uri(session=session, uri=uri)

            groups = OrganizationRepository.count_organization_invited_groups(session=session, uri=uri, group=group)

            return {'environments': environments, 'groups': groups, 'users': 0}

    @staticmethod
    def resolve_user_role(organization):
        context = get_context()
        if organization.owner == context.username:
            return OrganisationUserRole.Owner.value
        elif organization.SamlGroupName in context.groups:
            return OrganisationUserRole.Admin.value
        else:
            with context.db_engine.scoped_session() as session:
                if OrganizationRepository.find_group_membership(
                    session=session, organization=organization.organizationUri, groups=context.groups
                ):
                    return OrganisationUserRole.Invited.value
        return OrganisationUserRole.NotMember.value

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    @ResourcePolicyService.has_resource_permission(DELETE_ORGANIZATION)
    def archive_organization(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            org = OrganizationRepository.get_organization_by_uri(session, uri)
            environments = EnvironmentRepository.count_environments_with_organization_uri(session, uri)
            if environments:
                raise exceptions.UnauthorizedOperation(
                    action='ARCHIVE_ORGANIZATION',
                    message='The organization you tried to delete has linked environments',
                )
            session.delete(org)
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=org.SamlGroupName,
                resource_uri=org.organizationUri,
                resource_type=models.Organization.__name__,
            )

            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    @ResourcePolicyService.has_resource_permission(INVITE_ORGANIZATION_GROUP)
    def invite_group(uri, data):
        context = get_context()
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        with context.db_engine.scoped_session() as session:
            group: str = data['groupUri']

            organization = OrganizationRepository.get_organization_by_uri(session, uri)

            group_membership = OrganizationRepository.find_group_membership(
                session, [group], organization.organizationUri
            )
            if group_membership:
                raise exceptions.UnauthorizedOperation(
                    action='INVITE_TEAM',
                    message=f'Team {group} is already invited into the organization {organization.name}',
                )
            org_group = OrganizationGroup(
                organizationUri=organization.organizationUri,
                groupUri=group,
                invitedBy=context.username,
            )
            session.add(org_group)
            permissions = ORGANIZATION_INVITED_READONLY[:]
            permissions.extend(data.get('permissions', []))
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group,
                resource_uri=organization.organizationUri,
                permissions=permissions,
                resource_type=models.Organization.__name__,
            )

            return organization

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    @ResourcePolicyService.has_resource_permission(INVITE_ORGANIZATION_GROUP)
    def update_group(uri, data):
        context = get_context()
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        with context.db_engine.scoped_session() as session:
            group: str = data['groupUri']

            organization = OrganizationRepository.get_organization_by_uri(session, uri)

            group_membership = OrganizationRepository.find_group_membership(
                session, [group], organization.organizationUri
            )
            if group_membership is None:
                raise exceptions.UnauthorizedOperation(
                    action='UPDATE_TEAM',
                    message=f'Team {group} is not invited into the organization {organization.name}',
                )

            permissions = ORGANIZATION_INVITED_READONLY[:]
            permissions.extend(data.get('permissions', []))
            ResourcePolicyService.update_resource_policy(
                session=session,
                resource_uri=organization.organizationUri,
                resource_type=models.Organization.__name__,
                old_group=group,
                new_group=group,
                new_permissions=permissions,
            )

            return organization

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ORGANIZATIONS)
    @ResourcePolicyService.has_resource_permission(REMOVE_ORGANIZATION_GROUP)
    def remove_group(uri, group):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            organization = OrganizationRepository.get_organization_by_uri(session, uri)

            if group == organization.SamlGroupName:
                raise exceptions.UnauthorizedOperation(
                    action='REMOVE_TEAM',
                    message=f'Team: {group} is the owner of the organization {organization.name}',
                )

            group_env_objects_count = EnvironmentRepository.count_environments_with_organization_and_group(
                session=session, organization=organization, group=group
            )
            if group_env_objects_count > 0:
                raise exceptions.OrganizationResourcesFound(
                    action='Remove Team',
                    message=f'Team: {group} has {group_env_objects_count} linked environments on this environment.',
                )

            group_membership = OrganizationRepository.find_group_membership(
                session, [group], organization.organizationUri
            )
            if group_membership:
                session.delete(group_membership)
                session.commit()

            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=organization.organizationUri,
                resource_type=models.Organization.__name__,
            )
            return organization

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_ORGANIZATION)
    def list_organization_groups(filter, uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return OrganizationRepository.paginated_organization_groups(
                session=session,
                uri=uri,
                data=filter,
            )

    @staticmethod
    def resolve_organization_by_env(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env = EnvironmentRepository.get_environment_by_uri(session, uri)
            return OrganizationService.get_organization(uri=env.organizationUri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_ORGANIZATION)
    def list_group_organization_permissions(uri, groupUri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return ResourcePolicyService.get_resource_policy_permissions(
                session=session, group_uri=groupUri, resource_uri=uri
            )

    @staticmethod
    def list_invited_organization_permissions_with_descriptions():
        permissions = []
        with get_context().db_engine.scoped_session() as session:
            for p in ORGANIZATION_INVITED_DESCRIPTIONS:
                if PermissionRepository.find_permission_by_name(
                    session=session, permission_name=p, permission_type=PermissionType.RESOURCE.name
                ):
                    permissions.append({'name': p, 'description': ORGANIZATION_INVITED_DESCRIPTIONS[p]})
        return permissions
