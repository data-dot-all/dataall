import os
from .... import db
from ....api.constants import DashboardRole
from ....api.context import Context
from ....aws.handlers.quicksight import Quicksight
from ....aws.handlers.parameter_store import ParameterStoreManager
from ....db import permissions, models
from ....db.api import ResourcePolicy, Glossary, Vote
from ....searchproxy import indexers


def get_quicksight_reader_url(context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        dash: models.Dashboard = session.query(models.Dashboard).get(dashboardUri)
        env: models.Environment = session.query(models.Environment).get(
            dash.environmentUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=dash.dashboardUri,
            permission_name=permissions.GET_DASHBOARD,
        )
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=permissions.GET_DASHBOARD,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )
        if dash.SamlGroupName in context.groups:
            url = Quicksight.get_reader_session(
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                UserName=context.username,
                DashboardId=dash.DashboardId,
            )
        else:
            shared_groups = db.api.Dashboard.query_all_user_groups_shareddashboard(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=dashboardUri
            )
            if not shared_groups:
                raise db.exceptions.UnauthorizedOperation(
                    action=permissions.GET_DASHBOARD,
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
            permission_name=permissions.CREATE_DASHBOARD,
        )
        env: models.Environment = session.query(models.Environment).get(environmentUri)
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=permissions.CREATE_DASHBOARD,
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
            permission_name=permissions.CREATE_DASHBOARD,
        )
        env: models.Environment = db.api.Environment.get_environment_by_uri(
            session, input['environmentUri']
        )

        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=permissions.CREATE_DASHBOARD,
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
                action=permissions.CREATE_DASHBOARD,
                message=f'User: {context.username} has not AUTHOR rights on quicksight for the environment {env.label}',
            )

        input['environment'] = env
        dashboard = db.api.Dashboard.import_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=env.environmentUri,
            data=input,
            check_perm=True,
        )

        indexers.upsert_dashboard(session, context.es, dashboard.dashboardUri)

    return dashboard


def update_dashboard(context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        dashboard = db.api.Dashboard.get_dashboard_by_uri(
            session, input['dashboardUri']
        )
        input['dashboard'] = dashboard
        db.api.Dashboard.update_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data=input,
            check_perm=True,
        )

        indexers.upsert_dashboard(session, context.es, dashboard.dashboardUri)

        return dashboard


def list_dashboards(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Dashboard.paginated_user_dashboards(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def get_dashboard(context: Context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Dashboard.get_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: models.Dashboard):
    if context.username and source.owner == context.username:
        return DashboardRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DashboardRole.Admin.value
    return DashboardRole.Shared.value


def get_dashboard_organization(context: Context, source: models.Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        org = session.query(models.Organization).get(source.organizationUri)
    return org


def get_dashboard_environment(context: Context, source: models.Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        env = session.query(models.Environment).get(source.environmentUri)
    return env


def request_dashboard_share(
    context: Context,
    source: models.Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    with context.engine.scoped_session() as session:
        return db.api.Dashboard.request_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data={'principalId': principalId},
            check_perm=True,
        )


def approve_dashboard_share(
    context: Context,
    source: models.Dashboard,
    shareUri: str = None,
):
    with context.engine.scoped_session() as session:
        share = db.api.Dashboard.get_dashboard_share_by_uri(session, shareUri)
        dashboard = db.api.Dashboard.get_dashboard_by_uri(session, share.dashboardUri)
        return db.api.Dashboard.approve_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data={'share': share, 'shareUri': shareUri},
            check_perm=True,
        )


def reject_dashboard_share(
    context: Context,
    source: models.Dashboard,
    shareUri: str = None,
):
    with context.engine.scoped_session() as session:
        share = db.api.Dashboard.get_dashboard_share_by_uri(session, shareUri)
        dashboard = db.api.Dashboard.get_dashboard_by_uri(session, share.dashboardUri)
        return db.api.Dashboard.reject_dashboard_share(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboard.dashboardUri,
            data={'share': share, 'shareUri': shareUri},
            check_perm=True,
        )


def list_dashboard_shares(
    context: Context,
    source: models.Dashboard,
    dashboardUri: str = None,
    filter: dict = None,
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Dashboard.paginated_dashboard_shares(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=filter,
            check_perm=True,
        )


def share_dashboard(
    context: Context,
    source: models.Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    with context.engine.scoped_session() as session:
        return db.api.Dashboard.share_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data={'principalId': principalId},
            check_perm=True,
        )


def delete_dashboard(context: Context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        db.api.Dashboard.delete_dashboard(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dashboardUri,
            data=None,
            check_perm=True,
        )
        indexers.delete_doc(es=context.es, doc_id=dashboardUri)
        return True


def resolve_glossary_terms(context: Context, source: models.Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.dashboardUri, 'Dashboard'
        )


def resolve_upvotes(context: Context, source: models.Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Vote.count_upvotes(
            session, None, None, source.dashboardUri, data={'targetType': 'dashboard'}
        )
