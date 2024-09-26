from dataall.base.api import gql
from dataall.modules.dashboards.api.resolvers import (
    approve_dashboard_share,
    create_quicksight_data_source_set,
    delete_dashboard,
    import_dashboard,
    reject_dashboard_share,
    request_dashboard_share,
    update_dashboard,
)


importDashboard = gql.MutationField(
    name='importDashboard',
    type=gql.Ref('Dashboard'),
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('ImportDashboardInput')))],
    resolver=import_dashboard,
)

updateDashboard = gql.MutationField(
    name='updateDashboard',
    args=[
        gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('UpdateDashboardInput'))),
    ],
    type=gql.Ref('Dashboard'),
    resolver=update_dashboard,
)


deleteDashboard = gql.MutationField(
    name='deleteDashboard',
    type=gql.Boolean,
    args=[gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String))],
    resolver=delete_dashboard,
)

requestDashboardShare = gql.MutationField(
    name='requestDashboardShare',
    type=gql.Ref('DashboardShare'),
    args=[
        gql.Argument(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=request_dashboard_share,
)

approveDashboardShare = gql.MutationField(
    name='approveDashboardShare',
    type=gql.Ref('DashboardShare'),
    args=[
        gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=approve_dashboard_share,
)

rejectDashboardShare = gql.MutationField(
    name='rejectDashboardShare',
    type=gql.Ref('DashboardShare'),
    args=[
        gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=reject_dashboard_share,
)

createQuicksightDataSourceSet = gql.MutationField(
    name='createQuicksightDataSourceSet',
    args=[gql.Argument(name='vpcConnectionId', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=create_quicksight_data_source_set,
)
