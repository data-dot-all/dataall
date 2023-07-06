from dataall.base.api import gql

ImportDashboardInput = gql.InputType(
    name='ImportDashboardInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='SamlGroupName', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='dashboardId', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='terms', type=gql.ArrayType(gql.String)),
    ],
)

UpdateDashboardInput = gql.InputType(
    name='UpdateDashboardInput',
    arguments=[
        gql.Argument(name='dashboardUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='terms', type=gql.ArrayType(gql.String)),
    ],
)

DashboardFilter = gql.InputType(
    name='DashboardFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

DashboardShareFilter = gql.InputType(
    name='DashboardShareFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)
