from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.organizations.db import organization_models as models
from dataall.core.organizations.services.organization_service import OrganizationService


def create_organization(context: Context, source, input=None):
    if not input:
        raise exceptions.RequiredParameter(input)
    if not input.get('SamlGroupName'):
        raise exceptions.RequiredParameter('groupUri')
    if not input.get('label'):
        raise exceptions.RequiredParameter('label')

    return OrganizationService.create_organization(data=input)


def update_organization(context, source, organizationUri=None, input=None):
    return OrganizationService.update_organization(
        uri=organizationUri,
        data=input,
    )


def get_organization(context: Context, source, organizationUri=None):
    return OrganizationService.get_organization(uri=organizationUri)


def get_organization_simplified(context: Context, source, organizationUri=None):
    return OrganizationService.get_organization_simplified(uri=organizationUri)


def list_organizations(context: Context, source, filter=None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}

    return OrganizationService.list_organizations(filter)


def list_organization_environments(context, source, filter=None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}

    return OrganizationService.list_organization_environments(filter=filter, uri=source.organizationUri)


def stats(context, source: models.Organization, **kwargs):
    return OrganizationService.count_organization_resources(uri=source.organizationUri, group=source.SamlGroupName)


def resolve_user_role(context: Context, source: models.Organization):
    return OrganizationService.resolve_user_role(organization=source)


def archive_organization(context: Context, source, organizationUri: str = None):
    return OrganizationService.archive_organization(uri=organizationUri)


def invite_group(context: Context, source, input):
    if not input:
        raise exceptions.RequiredParameter(input)

    return OrganizationService.invite_group(uri=input['organizationUri'], data=input)


def update_group(context: Context, source, input):
    return OrganizationService.update_group(uri=input['organizationUri'], data=input)


def remove_group(context: Context, source, organizationUri=None, groupUri=None):
    return OrganizationService.remove_group(
        uri=organizationUri,
        group=groupUri,
    )


def list_organization_groups(context: Context, source, organizationUri=None, filter=None):
    if filter is None:
        filter = {}

    return OrganizationService.list_organization_groups(filter=filter, uri=organizationUri)


def resolve_organization_by_env(context, source, **kwargs):
    """
    Resolves the organization for environmental resource.
    """
    if not source:
        return None

    return OrganizationService.resolve_organization_by_env(uri=source.environmentUri)


def list_group_organization_permissions(context, source, organizationUri, groupUri):
    return OrganizationService.list_group_organization_permissions(uri=organizationUri, groupUri=groupUri)


def list_invited_organization_permissions_with_descriptions(context, source):
    return OrganizationService.list_invited_organization_permissions_with_descriptions()
