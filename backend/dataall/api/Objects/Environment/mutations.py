from .input_types import (
    ModifyEnvironmentInput,
    NewEnvironmentInput,
    EnableDataSubscriptionsInput,
    InviteGroupOnEnvironmentInput,
    AddConsumptionRoleToEnvironmentInput
)
from .resolvers import *

createEnvironment = gql.MutationField(
    name='createEnvironment',
    args=[gql.Argument(name='input', type=gql.NonNullableType(NewEnvironmentInput))],
    type=gql.Ref('Environment'),
    resolver=create_environment,
    test_scope='Environment',
)

updateEnvironment = gql.MutationField(
    name='updateEnvironment',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.NonNullableType(ModifyEnvironmentInput)),
    ],
    type=gql.Ref('Environment'),
    resolver=update_environment,
    test_scope='Environment',
)

inviteGroupOnEnvironment = gql.MutationField(
    name='inviteGroupOnEnvironment',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(InviteGroupOnEnvironmentInput)
        )
    ],
    type=gql.Ref('Environment'),
    resolver=invite_group,
)

addConsumptionRoleToEnvironment = gql.MutationField(
    name='addConsumptionRoleToEnvironment',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(AddConsumptionRoleToEnvironmentInput)
        )
    ],
    type=gql.Ref('ConsumptionRole'),
    resolver=add_consumption_role,
)

updateGroupPermission = gql.MutationField(
    name='updateGroupEnvironmentPermissions',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(InviteGroupOnEnvironmentInput)
        )
    ],
    type=gql.Ref('Environment'),
    resolver=update_group_permissions,
)

removeGroupFromEnvironment = gql.MutationField(
    name='removeGroupFromEnvironment',
    args=[
        gql.Argument('environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref('Environment'),
    resolver=remove_group,
)

removeConsumptionRoleFromEnvironment = gql.MutationField(
    name='removeConsumptionRoleFromEnvironment',
    args=[
        gql.Argument('environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('consumptionRoleUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=remove_consumption_role,
)

deleteEnvironment = gql.MutationField(
    name='deleteEnvironment',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    resolver=delete_environment,
    type=gql.Boolean,
)


EnableDataSubscriptions = gql.MutationField(
    name='enableDataSubscriptions',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=EnableDataSubscriptionsInput),
    ],
    resolver=enable_subscriptions,
    type=gql.Boolean,
)

DisableDataSubscriptions = gql.MutationField(
    name='DisableDataSubscriptions',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=disable_subscriptions,
    type=gql.Boolean,
)
