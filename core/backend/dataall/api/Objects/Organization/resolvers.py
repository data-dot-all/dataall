from .... import db
from ....api.constants import OrganisationUserRole
from ....api.context import Context
from ....db.api.organization import Organization
from ....db import models


def create_organization(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        organization = Organization.create_organization(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=input,
            check_perm=True,
        )
        return organization


def update_organization(context, source, organizationUri=None, input=None):
    with context.engine.scoped_session() as session:
        return Organization.update_organization(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=organizationUri,
            data=input,
            check_perm=True,
        )


def get_organization(context: Context, source, organizationUri=None):
    with context.engine.scoped_session() as session:
        return Organization.get_organization_by_uri(
            session=session, uri=organizationUri
        )


def list_organizations(context: Context, source, filter=None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}

    with context.engine.scoped_session() as session:
        return Organization.paginated_user_organizations(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def list_groups(context, source: models.Organization, filter=None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    with context.engine.scoped_session() as session:
        return Organization.paginated_organization_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.organizationUri,
            data=filter,
            check_perm=True,
        )


def list_organization_environments(context, source, filter=None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    with context.engine.scoped_session() as session:
        return Organization.paginated_organization_environments(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.organizationUri,
            data=filter,
            check_perm=True,
        )


def stats(context, source: models.Organization, **kwargs):
    with context.engine.scoped_session() as session:
        environments = db.api.Organization.count_organization_environments(
            session=session, uri=source.organizationUri
        )

        groups = db.api.Organization.count_organization_invited_groups(
            session=session, uri=source.organizationUri, group=source.SamlGroupName
        )

    return {'environments': environments, 'groups': groups, 'users': 0}


def resolve_user_role(context: Context, source: models.Organization):
    if source.owner == context.username:
        return OrganisationUserRole.Owner.value
    elif source.SamlGroupName in context.groups:
        return OrganisationUserRole.Admin.value
    else:
        with context.engine.scoped_session() as session:
            if Organization.find_organization_membership(
                session=session, uri=source.organizationUri, groups=context.groups
            ):
                return OrganisationUserRole.Invited.value
    return OrganisationUserRole.NoPermission.value


def archive_organization(context: Context, source, organizationUri: str = None):
    with context.engine.scoped_session() as session:
        return Organization.archive_organization(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=organizationUri,
            data=None,
            check_perm=True,
        )


def invite_group(context: Context, source, input):
    with context.engine.scoped_session() as session:
        organization, organization_group = db.api.Organization.invite_group(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['organizationUri'],
            data=input,
            check_perm=True,
        )
        return organization


def remove_group(context: Context, source, organizationUri=None, groupUri=None):
    with context.engine.scoped_session() as session:
        organization = db.api.Organization.remove_group(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=organizationUri,
            data={'groupUri': groupUri},
            check_perm=True,
        )
        return organization


def list_organization_invited_groups(
    context: Context, source, organizationUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Organization.paginated_organization_invited_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=organizationUri,
            data=filter,
            check_perm=True,
        )


def list_organization_groups(
    context: Context, source, organizationUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Organization.paginated_organization_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=organizationUri,
            data=filter,
            check_perm=True,
        )
