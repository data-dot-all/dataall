import logging

from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from backend.db.paginator import Page, paginate
from backend.db import (
    exceptions,
    core,
    common,
)
from backend.common.operations import (
    has_resource_perm,
    has_tenant_perm,
    ResourcePolicy,
)

from .. import permissions
from ..models.Organization import OrganisationUserRole

logger = logging.getLogger(__name__)


class Organization:
    @staticmethod
    def get_organization_by_uri(session, uri: str) -> core.models.Organization:
        if not uri:
            raise exceptions.RequiredParameter(param_name='organizationUri')
        org = Organization.find_organization_by_uri(session, uri)
        if not org:
            raise exceptions.ObjectNotFound('Organization', uri)
        return org

    @staticmethod
    def find_organization_by_uri(session, uri) -> core.models.Organization:
        return session.query(core.models.Organization).get(uri)

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    def create_organization(session, username, groups, uri, data=None, check_perm=None) -> core.models.Organization:
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('groupUri')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')

        org = core.models.Organization(
            label=data.get('label'),
            owner=username,
            tags=data.get('tags', []),
            description=data.get('description', 'No description provided'),
            SamlGroupName=data.get('SamlGroupName'),
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
        session.commit()
        member = core.models.OrganizationGroup(
            organizationUri=org.organizationUri,
            groupUri=data['SamlGroupName'],
        )
        session.add(member)

        activity = common.models.Activity(
            action='org:create',
            label='org:create',
            owner=username,
            summary=f'{username} create organization {org.name} ',
            targetUri=org.organizationUri,
            targetType='org',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlGroupName'],
            permissions=permissions.ORGANIZATION_ALL,
            resource_uri=org.organizationUri,
            resource_type=core.models.Organization.__name__,
        )

        return org

    @staticmethod
    @has_resource_perm(permissions.UPDATE_ORGANIZATION)
    def update_organization(session, username, groups, uri, data=None, check_perm=None):
        organization = Organization.get_organization_by_uri(session, uri)
        for field in data.keys():
            setattr(organization, field, data.get(field))
        session.commit()

        activity = common.models.Activity(
            action='org:update',
            label='org:create',
            owner=username,
            summary=f'{username} updated organization {organization.name} ',
            targetUri=organization.organizationUri,
            targetType='org',
        )
        session.add(activity)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=organization.SamlGroupName,
            permissions=permissions.ORGANIZATION_ALL,
            resource_uri=organization.organizationUri,
            resource_type=core.models.Organization.__name__,
        )
        return organization

    @staticmethod
    def query_user_organizations(session, username, groups, filter) -> Query:
        query = (
            session.query(core.models.Organization)
            .outerjoin(
                core.models.OrganizationGroup,
                core.models.Organization.organizationUri == core.models.OrganizationGroup.organizationUri,
            )
            .filter(
                or_(
                    core.models.Organization.owner == username,
                    core.models.OrganizationGroup.groupUri.in_(groups),
                )
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    core.models.Organization.label.ilike('%' + filter.get('term') + '%'),
                    core.models.Organization.description.ilike('%' + filter.get('term') + '%'),
                    core.models.Organization.tags.contains(f"{{{filter.get('term')}}}"),
                )
            )
        return query

    @staticmethod
    def paginated_user_organizations(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=Organization.query_user_organizations(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def query_organization_environments(session, uri, filter) -> Query:
        query = session.query(core.models.Environment).filter(core.models.Environment.organizationUri == uri)
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    core.models.Environment.label.ilike('%' + filter.get('term') + '%'),
                    core.models.Environment.description.ilike('%' + filter.get('term') + '%'),
                )
            )
        return query

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.GET_ORGANIZATION)
    def paginated_organization_environments(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=Organization.query_organization_environments(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.DELETE_ORGANIZATION)
    def archive_organization(session, username, groups, uri, data=None, check_perm=None) -> bool:

        org = Organization.get_organization_by_uri(session, uri)
        environments = session.query(core.models.Environment).filter(core.models.Environment.organizationUri == uri).count()
        if environments:
            raise exceptions.UnauthorizedOperation(
                action='ARCHIVE_ORGANIZATION',
                message='The organization you tried to delete has linked environments',
            )
        session.delete(org)
        ResourcePolicy.delete_resource_policy(
            session=session,
            group=org.SamlGroupName,
            resource_uri=org.organizationUri,
            resource_type=core.models.Organization.__name__,
        )

        return True

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.INVITE_ORGANIZATION_GROUP)
    def invite_group(
        session, username, groups, uri, data=None, check_perm=None
    ) -> (core.models.Organization, core.models.OrganizationGroup):

        Organization.validate_invite_params(data)

        group: str = data['groupUri']

        organization = Organization.get_organization_by_uri(session, uri)

        group_membership = Organization.find_group_membership(session, group, organization)
        if group_membership:
            raise exceptions.UnauthorizedOperation(
                action='INVITE_TEAM',
                message=f'Team {group} is already admin of the organization {organization.name}',
            )
        org_group = core.models.OrganizationGroup(
            organizationUri=organization.organizationUri,
            groupUri=group,
            invitedBy=username,
        )
        session.add(org_group)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group,
            resource_uri=organization.organizationUri,
            permissions=permissions.ORGANIZATION_INVITED,
            resource_type=core.models.Organization.__name__,
        )
        return organization, org_group

    @staticmethod
    def find_group_membership(session, group, organization):
        membership = (
            session.query(core.models.OrganizationGroup)
            .filter(
                (
                    and_(
                        core.models.OrganizationGroup.groupUri == group,
                        core.models.OrganizationGroup.organizationUri == organization.organizationUri,
                    )
                )
            )
            .first()
        )
        return membership

    @staticmethod
    def validate_invite_params(data):
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.REMOVE_ORGANIZATION_GROUP)
    def remove_group(session, username, groups, uri, data=None, check_perm=None):
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')

        group: str = data['groupUri']

        organization = Organization.get_organization_by_uri(session, uri)

        if group == organization.SamlGroupName:
            raise exceptions.UnauthorizedOperation(
                action='REMOVE_TEAM',
                message=f'Team: {group} is the owner of the organization {organization.name}',
            )

        group_env_objects_count = (
            session.query(core.models.Environment)
            .filter(
                and_(
                    core.models.Environment.organizationUri == organization.organizationUri,
                    core.models.Environment.SamlGroupName == group,
                )
            )
            .count()
        )
        if group_env_objects_count > 0:
            raise exceptions.OrganizationResourcesFound(
                action='Remove Team',
                message=f'Team: {group} has {group_env_objects_count} linked environments on this environment.',
            )

        group_membership = Organization.find_group_membership(session, group, organization)
        if group_membership:
            session.delete(group_membership)
            session.commit()

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=group,
            resource_uri=organization.organizationUri,
            resource_type=core.models.Organization.__name__,
        )
        return organization

    @staticmethod
    def query_organization_groups(session, uri, filter) -> Query:
        query = session.query(core.models.OrganizationGroup).filter(core.models.OrganizationGroup.organizationUri == uri)
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    core.models.OrganizationGroup.groupUri.ilike('%' + filter.get('term') + '%'),
                )
            )
        return query

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.GET_ORGANIZATION)
    def paginated_organization_groups(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=Organization.query_organization_groups(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def query_organization_invited_groups(session, organization, filter) -> Query:
        query = (
            session.query(core.models.OrganizationGroup)
            .join(
                core.models.Organization,
                core.models.OrganizationGroup.organizationUri == core.models.Organization.organizationUri,
            )
            .filter(
                and_(
                    core.models.Organization.organizationUri == organization.organizationUri,
                    core.models.OrganizationGroup.groupUri != core.models.Organization.SamlGroupName,
                )
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    core.models.OrganizationGroup.groupUri.ilike('%' + filter.get('term') + '%'),
                )
            )
        return query

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_ORGANIZATIONS)
    @has_resource_perm(permissions.GET_ORGANIZATION)
    def paginated_organization_invited_groups(session, username, groups, uri, data=None, check_perm=False) -> dict:
        organization = Organization.get_organization_by_uri(session, uri)
        return paginate(
            query=Organization.query_organization_invited_groups(session, organization, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def count_organization_invited_groups(session, uri, group) -> int:
        groups = (
            session.query(core.models.OrganizationGroup)
            .filter(
                and_(
                    core.models.OrganizationGroup.organizationUri == uri,
                    core.models.OrganizationGroup.groupUri != group,
                )
            )
            .count()
        )
        return groups

    @staticmethod
    def count_organization_environments(session, uri) -> int:
        envs = (
            session.query(core.models.Environment)
            .filter(
                core.models.Environment.organizationUri == uri,
            )
            .count()
        )
        return envs

    @staticmethod
    def find_organization_membership(session, uri, groups) -> int:
        groups = (
            session.query(core.models.OrganizationGroup)
            .filter(
                and_(
                    core.models.OrganizationGroup.organizationUri == uri,
                    core.models.OrganizationGroup.groupUri.in_(groups),
                )
            )
            .count()
        )
        if groups >= 1:
            return True
        else:
            return False
