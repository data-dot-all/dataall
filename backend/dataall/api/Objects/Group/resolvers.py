import os
import logging
from dataall import db
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.tenant_policy import TenantPolicy
from dataall.db import exceptions
from dataall.db.models import Group
from dataall.aws.handlers.cognito import Cognito

log = logging.getLogger()


def resolve_group_environment_permissions(context, source, environmentUri):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_group_permissions(
            session=session,
            uri=environmentUri,
            group_uri=source.groupUri
        )


def resolve_group_tenant_permissions(context, source):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return TenantPolicy.list_group_tenant_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.groupUri,
            data=None,
            check_perm=True,
        )


def get_group(context, source, groupUri):
    if not groupUri:
        exceptions.RequiredParameter('groupUri')
    return Group(groupUri=groupUri, name=groupUri, label=groupUri)


def list_cognito_groups(context, source, filter: dict = None):
    envname = os.getenv('envname', 'local')
    if envname in ['dkrcompose']:
        return [{"groupName": 'Engineers'}, {"groupName": 'Scientists'}, {"groupName": 'Requesters'}, {"groupName": 'Producers'}, {"groupName": 'Consumers'}]
    current_region = os.getenv('AWS_REGION', 'eu-west-1')
    groups = Cognito.list_cognito_groups(envname=envname, region=current_region)
    category, category_uri = filter.get("type"), filter.get("uri")
    if category and category_uri:
        if category == 'environment':
            with context.engine.scoped_session() as session:
                invited_groups = EnvironmentService.query_all_environment_groups(
                    session=session,
                    uri=category_uri,
                    filter=None,
                ).all()
        if category == 'organization':
            with context.engine.scoped_session() as session:
                organization = db.api.Organization.get_organization_by_uri(session, category_uri)
                invited_groups = db.api.Organization.query_organization_groups(
                    session=session,
                    uri=organization.organizationUri,
                    filter=None,
                ).all()
    invited_group_uris = [item.groupUri for item in invited_groups]
    res = []
    for group in groups:
        if group['GroupName'] not in invited_group_uris:
            res.append({"groupName": group['GroupName']})
    return res
