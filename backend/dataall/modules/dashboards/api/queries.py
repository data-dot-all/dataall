from dataall.base.api import gql
from dataall.modules.dashboards.api.resolvers import (
    get_dashboard,
    get_monitoring_dashboard_id,
    get_monitoring_vpc_connection_id,
    get_quicksight_designer_url,
    get_quicksight_reader_session,
    get_quicksight_reader_url,
    list_dashboard_shares,
    list_dashboards,
)

searchDashboards = gql.QueryField(
    name='searchDashboards',
    args=[gql.Argument(name='filter', type=gql.Ref('DashboardFilter'))],
    resolver=list_dashboards,
    type=gql.Ref('DashboardSearchResults'),
)

getDashboard = gql.QueryField(
    name='getDashboard',
    args=[gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Dashboard'),
    resolver=get_dashboard,
)

getMonitoringDashboardId = gql.QueryField(
    name='getMonitoringDashboardId',
    type=gql.String,
    resolver=get_monitoring_dashboard_id,
)

getMonitoringVpcConnectionId = gql.QueryField(
    name='getMonitoringVPCConnectionId',
    type=gql.String,
    resolver=get_monitoring_vpc_connection_id,
)


getPlatformReaderSession = gql.QueryField(
    name='getPlatformReaderSession',
    args=[
        gql.Argument(name='dashboardId', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_reader_session,
)

getAuthorSession = gql.QueryField(
    name='getAuthorSession',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_designer_url,
)


getReaderSession = gql.QueryField(
    name='getReaderSession',
    args=[gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_quicksight_reader_url,
)

listDashboardShares = gql.QueryField(
    name='listDashboardShares',
    args=[
        gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DashboardShareFilter')),
    ],
    resolver=list_dashboard_shares,
    type=gql.Ref('DashboardShareSearchResults'),
)
