from dataall.base.api import gql

NotificationFilter = gql.InputType(
    name='NotificationFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='read', type=gql.Boolean),
        gql.Argument(name='unread', type=gql.Boolean),
        gql.Argument(name='archived', type=gql.Boolean),
        gql.Argument(name='type', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)
