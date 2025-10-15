from dataall.base.api import gql

from dataall.core.environment.api.input_types import (
    ModifyEnvironmentInput,
    NewEnvironmentInput,
    EnableDataSubscriptionsInput,
    InviteGroupOnEnvironmentInput,
    AddConsumptionPrincipalToEnvironmentInput,
    UpdateConsumptionPrincipalInput,
)
from dataall.core.environment.api.resolvers import (
    add_consumption_principal,
    create_environment,
    delete_environment,
    disable_subscriptions,
    enable_subscriptions,
    invite_group,
    remove_consumption_principal,
    remove_group,
    update_consumption_principal,
    update_environment,
    update_group_permissions,
)

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
    args=[gql.Argument(name='input', type=gql.NonNullableType(InviteGroupOnEnvironmentInput))],
    type=gql.Ref('Environment'),
    resolver=invite_group,
)

addConsumptionPrincipalToEnvironment = gql.MutationField(
    name='addConsumptionPrincipalToEnvironment',
    args=[gql.Argument(name='input', type=gql.NonNullableType(AddConsumptionPrincipalToEnvironmentInput))],
    type=gql.Ref('ConsumptionPrincipal'),
    resolver=add_consumption_principal,
)

updateGroupPermission = gql.MutationField(
    name='updateGroupEnvironmentPermissions',
    args=[gql.Argument(name='input', type=gql.NonNullableType(InviteGroupOnEnvironmentInput))],
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

removeConsumptionPrincipalFromEnvironment = gql.MutationField(
    name='removeConsumptionPrincipalFromEnvironment',
    args=[
        gql.Argument('environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('consumptionPrincipalUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=remove_consumption_principal,
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

updateConsumptionPrincipal = gql.MutationField(
    name='updateConsumptionPrincipal',
    args=[
        gql.Argument('environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('consumptionPrincipalUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('input', type=UpdateConsumptionPrincipalInput),
    ],
    type=gql.Ref('ConsumptionPrincipal'),
    resolver=update_consumption_principal,
)
