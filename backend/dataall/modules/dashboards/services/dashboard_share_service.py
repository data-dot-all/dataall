from dataall.base.context import get_context
from dataall.base.db.exceptions import InvalidInput, UnauthorizedOperation
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.dashboards.db.dashboard_repositories import DashboardRepository
from dataall.modules.dashboards.db.dashboard_models import DashboardShareStatus, Dashboard
from dataall.modules.dashboards.services.dashboard_permissions import (
    SHARE_DASHBOARD,
    MANAGE_DASHBOARDS,
    GET_DASHBOARD,
    CREATE_DASHBOARD,
)


class DashboardShareService:
    @staticmethod
    def _get_dashboard_uri_by_share_uri(session, uri):
        share = DashboardRepository.get_dashboard_share_by_uri(session, uri)
        dashboard = DashboardRepository.get_dashboard_by_uri(session, share.dashboardUri)
        return dashboard.dashboardUri

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    def request_dashboard_share(uri: str, principal_id: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            if dashboard.SamlGroupName == principal_id:
                raise UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'Team {dashboard.SamlGroupName} is the owner of the dashboard {dashboard.label}',
                )

            share = DashboardRepository.find_share_for_group(session, dashboard.dashboardUri, principal_id)
            if not share:
                share = DashboardRepository.create_share(session, context.username, dashboard, principal_id)
            else:
                DashboardShareService._check_share_status(share)

                if share.status == DashboardShareStatus.REJECTED.value:
                    share.status = DashboardShareStatus.REQUESTED.value

            return share

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(SHARE_DASHBOARD, parent_resource=_get_dashboard_uri_by_share_uri)
    def approve_dashboard_share(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share = DashboardRepository.get_dashboard_share_by_uri(session, uri)
            DashboardShareService._change_share_status(share, DashboardShareStatus.APPROVED)
            DashboardShareService._create_share_policy(session, share.SamlGroupName, share.dashboardUri)
            return share

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(SHARE_DASHBOARD, parent_resource=_get_dashboard_uri_by_share_uri)
    def reject_dashboard_share(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share = DashboardRepository.get_dashboard_share_by_uri(session, uri)
            DashboardShareService._change_share_status(share, DashboardShareStatus.REJECTED)

            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=share.SamlGroupName,
                resource_uri=share.dashboardUri,
                resource_type=Dashboard.__name__,
            )

            return share

    @staticmethod
    def list_dashboard_shares(uri: str, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return DashboardRepository.paginated_dashboard_shares(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=uri,
                data=data,
            )

    @staticmethod
    def _change_share_status(share, status):
        DashboardShareService._check_share_status(share)
        if share.status == status.value:
            return share

        share.status = status.value

    @staticmethod
    def _check_share_status(share):
        if share.status not in DashboardShareStatus.__members__:
            raise InvalidInput(
                'Share status',
                share.status,
                str(DashboardShareStatus.__members__),
            )

    @staticmethod
    def _create_share_policy(session, principal_id, dashboard_uri):
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=principal_id,
            permissions=[GET_DASHBOARD],
            resource_uri=dashboard_uri,
            resource_type=Dashboard.__name__,
        )
