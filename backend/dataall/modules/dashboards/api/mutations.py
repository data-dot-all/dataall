from dataall.modules.dashboards.api.resolvers import *


importDashboard = gql.MutationField(
    name='importDashboard',
    type=gql.Ref('Dashboard'),
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('ImportDashboardInput'))
        )
    ],
    resolver=import_dashboard,
)

updateDashboard = gql.MutationField(
    name='updateDashboard',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('UpdateDashboardInput'))
        ),
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

createQuicksightDataSourceSet = gql.MutationField(
    name='createQuicksightDataSourceSet',
    args=[
        gql.Argument(name='vpcConnectionId', type=gql.NonNullableType(gql.String))
    ],
    type=gql.String,
    resolver=create_quicksight_data_source_set,
)
