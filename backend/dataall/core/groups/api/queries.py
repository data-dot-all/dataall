from dataall.base.api import gql
from dataall.core.groups.api.resolvers import get_group, list_groups, get_groups_for_user, list_user

getGroup = gql.QueryField(
    name='getGroup',
    args=[gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Group'),
    resolver=get_group,
)

listGroups = gql.QueryField(
    name='listGroups',
    args=[
        gql.Argument(name='filter', type=gql.Ref('ServiceProviderGroupFilter')),
    ],
    type=gql.ArrayType(gql.Ref('GroupsInfo')),
    resolver=list_groups,
)


getGroupsForUser = gql.QueryField(
    name='getGroupsForUser',
    args=[gql.Argument(name='userid', type=gql.NonNullableType(gql.String))],
    type=gql.ArrayType(gql.String),
    resolver=get_groups_for_user,
)


listUsersForGroup = gql.QueryField(
    name='listUsersForGroup',
    args=[gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String))],
    type=gql.ArrayType(gql.String),
    resolver=list_user,
)
