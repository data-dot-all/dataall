from ... import gql
from .resolvers import *
from .input_types import *

removeLFTag = gql.MutationField(
    name='removeLFTag',
    args=[
        gql.Argument('lftagUri', type=gql.NonNullableType(gql.String))
    ],
    type=gql.Boolean,
    resolver=remove_lf_tag,
)

addLFTag = gql.MutationField(
    name='addLFTag',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(AddLFTagInput)
        )
    ],
    type=gql.Ref('LFTag'),
    resolver=add_lf_tag,
)
