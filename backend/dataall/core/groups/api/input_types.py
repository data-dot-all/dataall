from dataall.base.api import gql

GroupFilter = gql.InputType(
    name='GroupFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

ServiceProviderGroupFilter = gql.InputType(
    name='ServiceProviderGroupFilter',
    arguments=[
        gql.Argument(name='type', type=gql.String),
        gql.Argument(name='uri', type=gql.String),
    ],
)
