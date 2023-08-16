from dataall.base.api import gql


UpdateGroupTenantPermissionsInput = gql.InputType(
    name='UpdateGroupTenantPermissionsInput',
    arguments=[
        gql.Argument('permissions', gql.ArrayType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
    ],
)
