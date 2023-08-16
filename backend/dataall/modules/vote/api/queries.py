from dataall.base.api import gql
from dataall.modules.vote.api.resolvers import count_upvotes, get_vote


countUpVotes = gql.QueryField(
    name='countUpVotes',
    type=gql.Integer,
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=count_upvotes,
)


getVote = gql.QueryField(
    name='getVote',
    type=gql.Ref('Vote'),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=get_vote,
)
