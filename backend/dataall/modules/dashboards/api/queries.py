from dataall.base.api import gql
from dataall.modules.dashboards.api.resolvers import *

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

getPlatformAuthorSession = gql.QueryField(
    name='getPlatformAuthorSession',
    args=[
        gql.Argument(name='awsAccount', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_author_session,
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
        gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String)),
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
