from dataall.base.api import gql

FeedMessageInput = gql.InputType(name='FeedMessageInput', arguments=[gql.Argument(name='content', type=gql.String)])

FeedMessageFilter = gql.InputType(
    name='FeedMessageFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)
