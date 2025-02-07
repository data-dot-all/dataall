from dataall.base.context import get_context
from dataall.core.activity.db.activity_models import Activity
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.base.db.exceptions import UnauthorizedOperation
from dataall.modules.dashboards.db.dashboard_repositories import DashboardRepository
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.dashboards.aws.dashboard_quicksight_client import DashboardQuicksightClient
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer
from dataall.modules.dashboards.services.dashboard_permissions import (
    MANAGE_DASHBOARDS,
    GET_DASHBOARD,
    UPDATE_DASHBOARD,
    CREATE_DASHBOARD,
    DASHBOARD_ALL,
    DELETE_DASHBOARD,
)


class DashboardService:
    """Service that serves request related to dashboard"""

    @staticmethod
    def get_dashboard(uri: str) -> Dashboard:
        with get_context().db_engine.scoped_session() as session:
            return DashboardRepository.get_dashboard_by_uri(session, uri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_DASHBOARD)
    def get_dashboard_restricted_information(uri: str, dashboard: Dashboard):
        return dashboard

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(CREATE_DASHBOARD)
    @GroupPolicyService.has_group_permission(CREATE_DASHBOARD)
    def import_dashboard(uri: str, admin_group: str, data: dict = None) -> Dashboard:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env = EnvironmentService.get_environment_by_uri(session, data['environmentUri'])
            enabled = EnvironmentService.get_boolean_env_param(session, env, 'dashboardsEnabled')

            if not enabled:
                raise UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'Dashboards feature is disabled for the environment {env.label}',
                )

            aws_client = DashboardQuicksightClient(context.username, env.AwsAccountId, env.region)
            can_import = aws_client.can_import_dashboard(data.get('dashboardId'))

            if not can_import:
                raise UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'User: {context.username} has not AUTHOR rights on quicksight for the environment {env.label}',
                )

            env = data.get('environment', EnvironmentService.get_environment_by_uri(session, uri))

            dashboard = DashboardRepository.create_dashboard(session, env, context.username, data)

            activity = Activity(
                action='DASHBOARD:CREATE',
                label='DASHBOARD:CREATE',
                owner=context.username,
                summary=f'{context.username} created dashboard {dashboard.label} in {env.label}',
                targetUri=dashboard.dashboardUri,
                targetType='dashboard',
            )
            session.add(activity)

            DashboardService._set_dashboard_resource_policy(session, env, dashboard, data['SamlGroupName'])

            DashboardService._update_glossary(session, dashboard, data)
            DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)
            return dashboard

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(UPDATE_DASHBOARD)
    def update_dashboard(uri: str, data: dict = None) -> Dashboard:
        with get_context().db_engine.scoped_session() as session:
            dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            for k in data.keys():
                setattr(dashboard, k, data.get(k))

            DashboardService._update_glossary(session, dashboard, data)
            environment = EnvironmentService.get_environment_by_uri(session, dashboard.environmentUri)
            DashboardService._set_dashboard_resource_policy(session, environment, dashboard, dashboard.SamlGroupName)

            DashboardIndexer.upsert(session, dashboard_uri=dashboard.dashboardUri)
            return dashboard

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(DELETE_DASHBOARD)
    def delete_dashboard(uri) -> bool:
        with get_context().db_engine.scoped_session() as session:
            dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            DashboardRepository.delete_dashboard(session, dashboard)

            ResourcePolicyService.delete_resource_policy(
                session=session, resource_uri=uri, group=dashboard.SamlGroupName
            )
            GlossaryRepository.delete_glossary_terms_links(
                session, target_uri=dashboard.dashboardUri, target_type='Dashboard'
            )
            VoteRepository.delete_votes(session, dashboard.dashboardUri, 'dashboard')

        DashboardIndexer.delete_doc(doc_id=uri)
        return True

    @staticmethod
    def _set_dashboard_resource_policy(session, environment, dashboard, group):
        DashboardService._attach_dashboard_policy(session, group, dashboard)
        if environment.SamlGroupName != dashboard.SamlGroupName:
            DashboardService._attach_dashboard_policy(session, environment.SamlGroupName, dashboard)

    @staticmethod
    def _attach_dashboard_policy(session, group: str, dashboard: Dashboard):
        ResourcePolicyService.attach_resource_policy(
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
            GlossaryRepository.set_glossary_terms_links(
                session,
                context.username,
                dashboard.dashboardUri,
                'Dashboard',
                data['terms'],
            )
