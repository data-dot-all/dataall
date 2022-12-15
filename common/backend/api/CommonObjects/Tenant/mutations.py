from ... import gql
from .input_types import UpdateGroupTenantPermissionsInput
from .resolvers import *

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

createQuicksightDataSourceSet = gql.MutationField(
    name='createQuicksightDataSourceSet',
    args=[
        gql.Argument(name='vpcConnectionId', type=gql.NonNullableType(gql.String))
    ],
    type=gql.String,
    resolver=create_quicksight_data_source_set,
)

updateSSMParameter = gql.MutationField(
    name='updateSSMParameter',
    args=[
        gql.Argument(name='name', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='value', type=gql.NonNullableType(gql.String))
    ],
    type=gql.String,
    resolver=update_ssm_parameter,
)
