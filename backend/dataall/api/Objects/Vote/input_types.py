from dataall.base.api import gql

VoteInput = gql.InputType(
    name='VoteInput',
    arguments=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='upvote', type=gql.NonNullableType(gql.Boolean)),
    ],
)
