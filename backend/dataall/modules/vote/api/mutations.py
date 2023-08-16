from dataall.base.api import gql
from dataall.modules.vote.api.resolvers import upvote


upVote = gql.MutationField(
    name='upVote',
    type=gql.Ref('Vote'),
    args=[
        gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('VoteInput'))),
    ],
    resolver=upvote,
)
