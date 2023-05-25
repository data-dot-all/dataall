import os
from dataall import db
from dataall.api.constants import DashboardRole
from dataall.api.context import Context
from dataall.aws.handlers.quicksight import Quicksight
from dataall.aws.handlers.parameter_store import ParameterStoreManager
from dataall.db import models
from dataall.db.api import ResourcePolicy, Glossary, Vote
from dataall.modules.dashboards.db.dashboard_repository import DashboardRepository
from dataall.modules.dashboards.db.models import Dashboard
from dataall.modules.dashboards.services.dashboard_permissions import GET_DASHBOARD, CREATE_DASHBOARD
from dataall.utils import Parameter
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer

param_store = Parameter()
ENVNAME = os.getenv("envname", "local")
DOMAIN_NAME = param_store.get_parameter(env=ENVNAME, path="frontend/custom_domain_name") if ENVNAME not in ["local", "dkrcompose"] else None
DOMAIN_URL = f"https://{DOMAIN_NAME}" if DOMAIN_NAME else "http://localhost:8080"


def get_quicksight_reader_url(context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        dash: Dashboard = session.query(Dashboard).get(dashboardUri)
        env: models.Environment = session.query(models.Environment).get(
            dash.environmentUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=dash.dashboardUri,
            permission_name=GET_DASHBOARD,
        )
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=GET_DASHBOARD,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )
        if dash.SamlGroupName in context.groups:
            url = Quicksight.get_reader_session(
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                UserName=context.username,
                DashboardId=dash.DashboardId,
                domain_name=DOMAIN_URL,
            )
        else:
            shared_groups = DashboardRepository.query_all_user_groups_shareddashboard(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=dashboardUri
            )
            if not shared_groups:
                raise db.exceptions.UnauthorizedOperation(
                    action=GET_DASHBOARD,
                    message='Dashboard has not been shared with your Teams',
                )

            session_type = ParameterStoreManager.get_parameter_value(
                parameter_path=f"/dataall/{os.getenv('envname', 'local')}/quicksight/sharedDashboardsSessions"
            )

            if session_type == 'reader':
                url = Quicksight.get_shared_reader_session(
                    AwsAccountId=env.AwsAccountId,
                    region=env.region,
                    UserName=context.username,
                    GroupName=shared_groups[0],
                    DashboardId=dash.DashboardId,
                )
            else:
                url = Quicksight.get_anonymous_session(
                    AwsAccountId=env.AwsAccountId,
                    region=env.region,
                    UserName=context.username,
                    DashboardId=dash.DashboardId,
                )
    return url


def get_quicksight_designer_url(
    context, source, environmentUri: str = None, dashboardUri: str = None
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=CREATE_DASHBOARD,
        )
        env: models.Environment = session.query(models.Environment).get(environmentUri)
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=CREATE_DASHBOARD,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )

        url = Quicksight.get_author_session(
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            UserName=context.username,
            UserRole='AUTHOR',
        )

    return url


def import_dashboard(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=input['environmentUri'],
            permission_name=CREATE_DASHBOARD,
        )
        env: models.Environment = db.api.Environment.get_environment_by_uri(
            session, input['environmentUri']
        )

        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=CREATE_DASHBOARD,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )

        can_import = Quicksight.can_import_dashboard(
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            UserName=context.username,
            DashboardId=input.get('dashboardId'),
        )

        if not can_import:
            raise db.exceptions.UnauthorizedOperation(
                action=CREATE_DASHBOARD,
                message=f'User: {context.username} has not AUTHOR rights on quicksight for the environment {env.label}',
            )

        input['environment'] = env
        dashboard = DashboardRepository.import_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=env.environmentUri,
            data=input,
            check_perm=True,
        )

        DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)

    return dashboard


def update_dashboard(context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        dashboard = DashboardRepository.get_dashboard_by_uri(
            session, input['dashboardUri']
        )
        input['dashboard'] = dashboard
        DashboardRepository.update_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data=input,
            check_perm=True,
        )

        DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)

        return dashboard


def list_dashboards(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DashboardRepository.paginated_user_dashboards(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def get_dashboard(context: Context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        return DashboardRepository.get_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: Dashboard):
    if context.username and source.owner == context.username:
        return DashboardRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DashboardRole.Admin.value
    return DashboardRole.Shared.value


def get_dashboard_organization(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        org = session.query(models.Organization).get(source.organizationUri)
    return org


def request_dashboard_share(
    context: Context,
    source: Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    with context.engine.scoped_session() as session:
        return DashboardRepository.request_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data={'principalId': principalId},
            check_perm=True,
        )


def approve_dashboard_share(
    context: Context,
    source: Dashboard,
    shareUri: str = None,
):
    with context.engine.scoped_session() as session:
        share = DashboardRepository.get_dashboard_share_by_uri(session, shareUri)
        dashboard = DashboardRepository.get_dashboard_by_uri(session, share.dashboardUri)
        return DashboardRepository.approve_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data={'share': share, 'shareUri': shareUri},
            check_perm=True,
        )


def reject_dashboard_share(
    context: Context,
    source: Dashboard,
    shareUri: str = None,
):
    with context.engine.scoped_session() as session:
        share = DashboardRepository.get_dashboard_share_by_uri(session, shareUri)
        dashboard = DashboardRepository.get_dashboard_by_uri(session, share.dashboardUri)
        return DashboardRepository.reject_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data={'share': share, 'shareUri': shareUri},
            check_perm=True,
        )


def list_dashboard_shares(
    context: Context,
    source: Dashboard,
    dashboardUri: str = None,
    filter: dict = None,
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DashboardRepository.paginated_dashboard_shares(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=filter,
            check_perm=True,
        )


def share_dashboard(
    context: Context,
    source: Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    with context.engine.scoped_session() as session:
        return DashboardRepository.share_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data={'principalId': principalId},
            check_perm=True,
        )


def delete_dashboard(context: Context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        DashboardRepository.delete_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=None,
            check_perm=True,
        )
        DashboardIndexer.delete_doc(doc_id=dashboardUri)
        return True


def resolve_glossary_terms(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.dashboardUri, 'Dashboard'
        )


def resolve_upvotes(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Vote.count_upvotes(
            session, None, None, source.dashboardUri, data={'targetType': 'dashboard'}
        )
