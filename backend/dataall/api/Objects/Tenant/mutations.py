from ... import gql
from .input_types import UpdateGroupTenantPermissionsInput
from .resolvers import update_group_permissions

updateGroupPermission = gql.MutationField(
    name='updateGroupTenantPermissions',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(UpdateGroupTenantPermissionsInput)
        )
    ],
    type=gql.Boolean,
    resolver=update_group_permissions,
)
