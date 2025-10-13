from dataall.base.api.context import Context
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.base.db.exceptions import RequiredParameter
from dataall.modules.dashboards.api.enums import DashboardRole
from dataall.modules.dashboards.db.dashboard_repositories import DashboardRepository
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.dashboards.services.dashboard_quicksight_service import DashboardQuicksightService
from dataall.modules.dashboards.services.dashboard_service import DashboardService
from dataall.modules.dashboards.services.dashboard_share_service import DashboardShareService


def import_dashboard(context: Context, source, input: dict = None):
    if not input:
        raise RequiredParameter(input)
    if not input.get('environmentUri'):
        raise RequiredParameter('environmentUri')
    if not input.get('SamlGroupName'):
        raise RequiredParameter('group')
    if not input.get('dashboardId'):
        raise RequiredParameter('dashboardId')
    if not input.get('label'):
        raise RequiredParameter('label')

    return DashboardService.import_dashboard(
        uri=input['environmentUri'], admin_group=input['SamlGroupName'], data=input
    )


def update_dashboard(context, source, input: dict = None):
    return DashboardService.update_dashboard(uri=input['dashboardUri'], data=input)


def list_dashboards(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DashboardRepository.paginated_user_dashboards(
            session=session,
            username=context.username,
            groups=context.groups,
            data=filter,
        )


def get_dashboard(context: Context, source, dashboardUri: str = None):
    return DashboardService.get_dashboard(uri=dashboardUri)


def get_dashboard_restricted_information(context: Context, source: Dashboard):
    if not source:
        return None
    return DashboardService.get_dashboard_restricted_information(uri=source.dashboardUri, dashboard=source)


def resolve_user_role(context: Context, source: Dashboard):
    if context.username and source.owner == context.username:
        return DashboardRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DashboardRole.Admin.value
    return DashboardRole.Shared.value


def get_dashboard_organization(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return OrganizationRepository.get_organization_by_uri(session, source.organizationUri)


def request_dashboard_share(
    context: Context,
    source: Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    return DashboardShareService.request_dashboard_share(uri=dashboardUri, principal_id=principalId)


def approve_dashboard_share(context: Context, source: Dashboard, shareUri: str = None):
    return DashboardShareService.approve_dashboard_share(uri=shareUri)


def reject_dashboard_share(context: Context, source: Dashboard, shareUri: str = None):
    return DashboardShareService.reject_dashboard_share(uri=shareUri)


def list_dashboard_shares(
    context: Context,
    source: Dashboard,
    dashboardUri: str = None,
    filter: dict = None,
):
    if not filter:
        filter = {}
    return DashboardShareService.list_dashboard_shares(uri=dashboardUri, data=filter)


def delete_dashboard(context: Context, source, dashboardUri: str = None):
    return DashboardService.delete_dashboard(uri=dashboardUri)


def resolve_glossary_terms(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.dashboardUri, 'Dashboard')


def resolve_upvotes(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return VoteRepository.count_upvotes(session, source.dashboardUri, target_type='dashboard')


def get_monitoring_dashboard_id(context, source):
    return DashboardQuicksightService.get_monitoring_dashboard_id()


def get_monitoring_vpc_connection_id(context, source):
    return DashboardQuicksightService.get_monitoring_vpc_connection_id()


def create_quicksight_data_source_set(context, source, vpcConnectionId: str = None):
    return DashboardQuicksightService.create_quicksight_data_source_set(vpcConnectionId)


def get_quicksight_reader_session(context, source, dashboardId: str = None):
    return DashboardQuicksightService.get_quicksight_reader_session(dashboardId)


def get_quicksight_reader_url(context, source, dashboardUri: str = None):
    return DashboardQuicksightService.get_quicksight_reader_url(uri=dashboardUri)


def get_quicksight_designer_url(context, source, environmentUri: str):
    return DashboardQuicksightService.get_quicksight_designer_url(uri=environmentUri)
