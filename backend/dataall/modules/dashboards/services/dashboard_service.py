from dataall.aws.handlers.quicksight import Quicksight
from dataall.core.context import get_context
from dataall.core.permission_checker import has_tenant_permission, has_resource_permission, has_group_permission
from dataall.db.api import ResourcePolicy, Glossary, Vote, Environment
from dataall.db.exceptions import UnauthorizedOperation
from dataall.db.models import Activity
from dataall.modules.dashboards import DashboardRepository, Dashboard
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer
from dataall.modules.dashboards.services.dashboard_permissions import MANAGE_DASHBOARDS, GET_DASHBOARD, \
    UPDATE_DASHBOARD, CREATE_DASHBOARD, DASHBOARD_ALL


class DashboardService:
    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(GET_DASHBOARD)
    def get_dashboard(uri: str) -> Dashboard:
        with get_context().db_engine.scoped_session() as session:
            return DashboardRepository.get_dashboard_by_uri(session, uri)

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(CREATE_DASHBOARD)
    def import_dashboard(uri: str, data: dict = None) -> Dashboard:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env = Environment.get_environment_by_uri(session, data['environmentUri'])

            if not env.dashboardsEnabled:
                raise UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'Dashboards feature is disabled for the environment {env.label}',
                )

            can_import = Quicksight.can_import_dashboard(
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                UserName=context.username,
                DashboardId=data.get('dashboardId'),
            )

            if not can_import:
                raise db.exceptions.UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'User: {context.username} has not AUTHOR rights on quicksight for the environment {env.label}',
                )
            Environment.check_group_environment_permission(
                session=session,
                username=username,
                groups=groups,
                uri=uri,
                group=data['SamlGroupName'],
                permission_name=CREATE_DASHBOARD,
            )

            env = data.get(
                'environment', Environment.get_environment_by_uri(session, uri)
            )

            dashboard = DashboardRepository.create_dashboard(session, env, context.username, data)

            activity = Activity(
                action='DASHBOARD:CREATE',
                label='DASHBOARD:CREATE',
                owner=username,
                summary=f'{username} created dashboard {dashboard.label} in {env.label}',
                targetUri=dashboard.dashboardUri,
                targetType='dashboard',
            )
            session.add(activity)

            DashboardService._set_dashboard_resource_policy(
                session, env, dashboard, data['SamlGroupName']
            )

            DashboardService._update_glossary(session, dashboard, data)
            DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)
            return dashboard

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(UPDATE_DASHBOARD)
    def update_dashboard(uri: str, data: dict = None) -> Dashboard:
        with get_context().db_engine.scoped_session() as session:
            dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            for k in data.keys():
                setattr(dashboard, k, data.get(k))

            DashboardService._update_glossary(session, dashboard, data)
            environment = Environment.get_environment_by_uri(session, dashboard.environmentUri)
            DashboardService._set_dashboard_resource_policy(
                session, environment, dashboard, dashboard.SamlGroupName
            )

            DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)
            return dashboard

    @staticmethod
    def delete_dashboard(uri) -> bool:
        # TODO THERE WAS NO PERMISSION CHECK
        with get_context().db_engine.scoped_session() as session:
            dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            DashboardRepository.delete_dashboard(session, dashboard.dashboardUri)

            ResourcePolicy.delete_resource_policy(
                session=session, resource_uri=uri, group=dashboard.SamlGroupName
            )
            Glossary.delete_glossary_terms_links(
                session, target_uri=dashboard.dashboardUri, target_type='Dashboard'
            )
            Vote.delete_votes(session, dashboard.dashboardUri, 'dashboard')

        DashboardIndexer.delete_doc(doc_id=uri)
        return True

    @staticmethod
    def _set_dashboard_resource_policy(session, environment, dashboard, group):
        DashboardService._attach_dashboard_policy(session, group, dashboard)
        if environment.SamlGroupName != dashboard.SamlGroupName:
            DashboardService._attach_dashboard_policy(session, environment.SamlGroupName, dashboard)

    @staticmethod
    def _attach_dashboard_policy(session, group: str, dashboard: Dashboard):
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group,
            permissions=DASHBOARD_ALL,
            resource_uri=dashboard.dashboardUri,
            resource_type=Dashboard.__name__,
        )

    @staticmethod
    def _update_glossary(session, dashboard, data):
        context = get_context()
        if 'terms' in data:
            Glossary.set_glossary_terms_links(
                session,
                context.username,
                dashboard.dashboardUri,
                'Dashboard',
                data['terms'],
            )

