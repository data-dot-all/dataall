from .resolvers import *

getShareObject = gql.QueryField(
    name='getShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('ShareObject'),
    resolver=get_share_object,
)


getShareRequestsFromMe = gql.QueryField(
    name='getShareRequestsFromMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('ShareSearchResult'),
    resolver=list_shares_in_my_outbox,
)

getLFTagShareRequestsFromMe = gql.QueryField(
    name='getLFTagShareRequestsFromMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('LFTagShareSearchResult'),
    resolver=list_lftag_shares_in_my_outbox,
)

getShareRequestsToMe = gql.QueryField(
    name='getShareRequestsToMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('ShareSearchResult'),
    resolver=list_shares_in_my_inbox,
)

getLFTagShareRequestsToMe = gql.QueryField(
    name='getLFTagShareRequestsToMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('LFTagShareSearchResult'),
    resolver=list_lftag_shares_in_my_inbox,
)

getLFTagShareObject = gql.QueryField(
    name='getLFTagShareObject',
    args=[gql.Argument(name='lftagShareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('LFTagShareObject'),
    resolver=get_lf_tag_share_object,
)