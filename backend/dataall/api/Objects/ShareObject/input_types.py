from ....api.constants import *


NewShareObjectInput = gql.InputType(
    name='NewShareObjectInput',
    arguments=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='principalType', type=gql.NonNullableType(gql.String)),
    ],
)


AddSharedItemInput = gql.InputType(
    name='AddSharedItemInput',
    arguments=[
        gql.Argument(name='itemUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(
            name='itemType', type=gql.NonNullableType(ShareableType.toGraphQLEnum())
        ),
    ],
)


class ShareSortField(GraphQLEnumMapper):
    created = 'created'
    updated = 'updated'
    label = 'label'


ShareSortCriteria = gql.InputType(
    name='ShareSortCriteria',
    arguments=[
        gql.Argument(
            name='field', type=gql.NonNullableType(ShareSortField.toGraphQLEnum())
        ),
        gql.Argument(
            name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())
        ),
    ],
)

ShareObjectFilter = gql.InputType(
    name='ShareObjectFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('sort', gql.ArrayType(ShareSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('roles', gql.ArrayType(OrganisationUserRole.toGraphQLEnum())),
        gql.Argument('tags', gql.ArrayType(gql.String)),
    ],
)


ShareableObjectFilter = gql.InputType(
    name='ShareableObjectFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument(name='isShared', type=gql.Boolean),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
