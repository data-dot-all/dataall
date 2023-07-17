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

getShareRequestsToMe = gql.QueryField(
    name='getShareRequestsToMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('ShareSearchResult'),
    resolver=list_shares_in_my_inbox,
)
