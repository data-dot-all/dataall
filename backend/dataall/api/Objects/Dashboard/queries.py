from ... import gql
from .resolvers import *

searchDashboards = gql.QueryField(
    name="searchDashboards",
    args=[gql.Argument(name="filter", type=gql.Ref("DashboardFilter"))],
    resolver=list_dashboards,
    type=gql.Ref("DashboardSearchResults"),
)

getDashboard = gql.QueryField(
    name="getDashboard",
    args=[gql.Argument(name="dashboardUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("Dashboard"),
    resolver=get_dashboard,
)


getAuthorSession = gql.QueryField(
    name="getAuthorSession",
    args=[
        gql.Argument(name="dashboardUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="environmentUri", type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_designer_url,
)


getReaderSession = gql.QueryField(
    name="getReaderSession",
    args=[gql.Argument(name="dashboardUri", type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_quicksight_reader_url,
)

listDashboardShares = gql.QueryField(
    name="listDashboardShares",
    args=[
        gql.Argument(name="dashboardUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="filter", type=gql.Ref("DashboardShareFilter")),
    ],
    resolver=list_dashboard_shares,
    type=gql.Ref("DashboardShareSearchResults"),
)
