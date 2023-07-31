from dataall.base.api import gql

Vote = gql.ObjectType(
    name='Vote',
    fields=[
        gql.Field(name='voteUri', type=gql.ID),
        gql.Field(name='targetType', type=gql.String),
        gql.Field(name='targetUri', type=gql.String),
        gql.Field(name='upvote', type=gql.Boolean),
        gql.Field(name='created', type=gql.String),
    ],
)
