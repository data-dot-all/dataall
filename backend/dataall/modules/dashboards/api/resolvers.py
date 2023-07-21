from dataall.base.api.graphql_api import api_mutation, api_query
from dataall.base.context import get_context
from dataall.core.catalog.db.glossary import Glossary
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization import Organization
from dataall.core.vote.db.vote import Vote
from dataall.modules.dashboards.api.dashboard_schema import UpdateDashboardInput, ImportDashboardInput, DashboardFilter, \
    DashboardSearchResults, DashboardShareDto, DashboardShareFilter, DashboardShareSearchResults, DashboardDto
from dataall.modules.dashboards.api.enums import DashboardRole
from dataall.modules.dashboards.db.dashboard_repository import DashboardRepository
from dataall.modules.dashboards.services.dashboard_quicksight_service import DashboardQuicksightService
from dataall.modules.dashboards.services.dashboard_service import DashboardService
from dataall.modules.dashboards.services.dashboard_share_service import DashboardShareService


@api_mutation("importDashboard")
def import_dashboard(input: ImportDashboardInput) -> DashboardDto:
    return DashboardService.import_dashboard(
        uri=input.environmentUri,
        admin_group=input.SamlGroupName,
        data=input
    )


@api_mutation("updateDashboard")
def update_dashboard(input: UpdateDashboardInput) -> DashboardDto:
    return DashboardService.update_dashboard(uri=input.dashboardUri, data=input)


@api_query("searchDashboards")
def list_dashboards(filter: DashboardFilter) -> DashboardSearchResults:
    context = get_context()
    with context.db_engine.scoped_session() as session:
        page: dict = DashboardRepository.paginated_user_dashboards(
            session=session,
            username=context.username,
            groups=context.groups,
            data=filter,
        )
        return DashboardSearchResults(**page)


@api_query("getDashboard")
def get_dashboard(dashboardUri: str) -> DashboardDto:
    context = get_context()
    with context.db_engine.scoped_session() as session:
        dashboard = DashboardService.get_dashboard(uri=dashboardUri)

        role = DashboardRole.Shared.value
        if context.username and dashboard.owner == context.username:
             role = DashboardRole.Creator.value
        elif context.groups and dashboard.SamlGroupName in context.groups:
            role = DashboardRole.Admin.value

        return DashboardDto(
            dashboard=dashboard,
            upvotes=Vote.count_upvotes(
                session, dashboard.dashboardUri, target_type='dashboard'
            ),
            terms= Glossary.get_glossary_terms_links(
                session, dashboard.dashboardUri, 'Dashboard'
            ),
            organization=Organization.get_organization_by_uri(session, dashboard.organizationUri),
            environment=EnvironmentService.get_environment_by_uri(session, dashboard.environmentUri),
            role=role
        )


@api_mutation(name="requestDashboardShare")
def request_dashboard_share(principalId: str, dashboardUri: str) -> DashboardShareDto:
    return DashboardShareService.request_dashboard_share(uri=dashboardUri, principal_id=principalId)


@api_mutation(name="approveDashboardShare")
def approve_dashboard_share(shareUri: str) -> DashboardShareDto:
    return DashboardShareService.approve_dashboard_share(uri=shareUri)


@api_mutation(name="rejectDashboardShare")
def reject_dashboard_share(shareUri: str) -> DashboardShareDto:
    return DashboardShareService.reject_dashboard_share(uri=shareUri)


@api_query(name="listDashboardShares")
def list_dashboard_shares(dashboardUri: str, filter: DashboardShareFilter) -> DashboardShareSearchResults:
    return DashboardShareService.list_dashboard_shares(uri=dashboardUri, data=filter)


@api_mutation("shareDashboard")
def share_dashboard(principalId: str, dashboardUri: str) -> DashboardShareDto:
    return DashboardShareService.share_dashboard(uri=dashboardUri, principal_id=principalId)


@api_mutation("deleteDashboard")
def delete_dashboard(dashboardUri: str) -> bool:
    return DashboardService.delete_dashboard(uri=dashboardUri)


@api_query("getMonitoringDashboardId")
def get_monitoring_dashboard_id() -> str:
    return DashboardQuicksightService.get_monitoring_dashboard_id()


@api_query("getMonitoringVPCConnectionId")
def get_monitoring_vpc_connection_id() -> str:
    return DashboardQuicksightService.get_monitoring_vpc_connection_id()


@api_mutation("vpcConnectionId")
def create_quicksight_data_source_set(vpcConnectionId: str) -> str:
    return DashboardQuicksightService.create_quicksight_data_source_set(vpcConnectionId)


@api_query("getPlatformAuthorSession")
def get_quicksight_author_session(awsAccount: str) -> str:
    return DashboardQuicksightService.get_quicksight_author_session(awsAccount)


@api_query("getPlatformReaderSession")
def get_quicksight_reader_session(dashboardId: str) -> str:
    return DashboardQuicksightService.get_quicksight_reader_session(dashboardId)


@api_query("getReaderSession")
def get_quicksight_reader_url(dashboardUri: str) -> str:
    return DashboardQuicksightService.get_quicksight_reader_url(uri=dashboardUri)


@api_query("getAuthorSession")
def get_quicksight_designer_url(environmentUri: str) -> str:
    return DashboardQuicksightService.get_quicksight_designer_url(uri=environmentUri)
