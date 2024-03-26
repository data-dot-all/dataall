from dataall.base.api import gql
from .input_types import UpdateGroupTenantPermissionsInput
from .resolvers import update_group_permissions, update_ssm_parameter


updateGroupPermission = gql.MutationField(
    name='updateGroupTenantPermissions',
    args=[gql.Argument(name='input', type=gql.NonNullableType(UpdateGroupTenantPermissionsInput))],
    type=gql.Boolean,
    resolver=update_group_permissions,
)

updateSSMParameter = gql.MutationField(
    name='updateSSMParameter',
    args=[
        gql.Argument(name='name', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='value', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=update_ssm_parameter,
)
