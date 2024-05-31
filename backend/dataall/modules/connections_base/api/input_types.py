from dataall.base.api import gql


ConnectionFilter = gql.InputType(
    name='ConnectionFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument(name='environmentUri', type=gql.String),
    ],
)

