from ... import gql

GroupFilter = gql.InputType(
    name='GroupFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

CognitoGroupFilter = gql.InputType(
    name='CognitoGroupFilter',
    arguments=[
        gql.Argument(name='type', type=gql.String),
        gql.Argument(name='uri', type=gql.String),
    ],
)
