from dataall.base.api import gql
from .resolvers import *


listUserActivities = gql.QueryField(
    name='listUserActivities',
    type=gql.Ref('ActivitySearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('ActivityFilter'))],
    resolver=list_user_activities,
)
