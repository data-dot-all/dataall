from dataall import gql
from .resolvers import *


upVote = gql.MutationField(
    name='upVote',
    type=gql.Ref('Vote'),
    args=[
        gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('VoteInput'))),
    ],
    resolver=upvote,
)
