from dataall.base.api import gql
from dataall.core.cognito_groups.api.resolvers import get_group, list_cognito_groups

getGroup = gql.QueryField(
    name='getGroup',
    args=[gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Group'),
    resolver=get_group,
)

listCognitoGroups = gql.QueryField(
    name='listCognitoGroups',
    args=[
        gql.Argument(name='filter', type=gql.Ref('CognitoGroupFilter')),
    ],
    type=gql.ArrayType(gql.Ref('CognitoGroup')),
    resolver=list_cognito_groups
)
