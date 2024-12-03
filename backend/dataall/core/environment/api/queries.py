from dataall.base.api import gql

from dataall.core.environment.api.input_types import EnvironmentFilter
from dataall.core.environment.api.resolvers import (
    generate_environment_access_token,
    get_cdk_exec_policy_template,
    get_environment,
    get_environment_assume_role_url,
    get_external_id,
    get_pivot_role_name,
    get_pivot_role_template,
    get_trust_account,
    list_all_environment_consumption_roles,
    list_all_environment_groups,
    list_consumption_roles,
    list_environment_consumption_roles,
    list_environment_group_invitation_permissions,
    list_environment_groups,
    list_environment_invited_groups,
    list_environment_networks,
    list_environments,
    list_groups,
    list_valid_environments,
    get_consumption_role_policies,
)
from dataall.core.environment.api.types import (
    Environment,
    EnvironmentSearchResult,
    EnvironmentSimplifiedSearchResult,
    RoleManagedPolicy,
)

getTrustAccount = gql.QueryField(
    name='getTrustAccount',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_trust_account,
    test_scope='Environment',
)

getEnvironment = gql.QueryField(
    name='getEnvironment',
    args=[gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String))],
    type=gql.Thunk(lambda: Environment),
    resolver=get_environment,
    test_scope='Environment',
)


listEnvironments = gql.QueryField(
    name='listEnvironments',
    args=[gql.Argument('filter', EnvironmentFilter)],
    type=EnvironmentSearchResult,
    resolver=list_environments,
    test_scope='Environment',
)


listValidEnvironments = gql.QueryField(
    name='listValidEnvironments',
    args=[gql.Argument('filter', EnvironmentFilter)],
    type=EnvironmentSimplifiedSearchResult,
    resolver=list_valid_environments,
    test_scope='Environment',
)


listEnvironmentNetworks = gql.QueryField(
    name='listEnvironmentNetworks',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('VpcFilter')),
    ],
    resolver=list_environment_networks,
    type=gql.Ref('VpcSearchResult'),
    test_scope='Environment',
)


generateEnvironmentAccessToken = gql.QueryField(
    name='generateEnvironmentAccessToken',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.String),
    ],
    type=gql.String,
    resolver=generate_environment_access_token,
    test_scope='Environment',
)


getEnvironmentAssumeRoleUrl = gql.QueryField(
    name='getEnvironmentAssumeRoleUrl',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.String),
    ],
    type=gql.String,
    resolver=get_environment_assume_role_url,
    test_scope='Environment',
)


listEnvironmentInvitedGroups = gql.QueryField(
    name='listEnvironmentInvitedGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_environment_invited_groups,
)

listEnvironmentGroups = gql.QueryField(
    name='listEnvironmentGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_environment_groups,
)

listAllEnvironmentGroups = gql.QueryField(
    name='listAllEnvironmentGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_all_environment_groups,
)

listAllGroups = gql.QueryField(
    name='listAllGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_groups,
)

listAllConsumptionRoles = gql.QueryField(
    name='listAllConsumptionRoles',
    type=gql.Ref('ConsumptionRoleSearchResult'),
    args=[
        gql.Argument(name='filter', type=gql.Ref('ConsumptionRoleFilter')),
    ],
    resolver=list_consumption_roles,
)

listEnvironmentConsumptionRoles = gql.QueryField(
    name='listEnvironmentConsumptionRoles',
    type=gql.Ref('ConsumptionRoleSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('ConsumptionRoleFilter')),
    ],
    resolver=list_environment_consumption_roles,
)


listAllEnvironmentConsumptionRoles = gql.QueryField(
    name='listAllEnvironmentConsumptionRoles',
    type=gql.Ref('ConsumptionRoleSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('ConsumptionRoleFilter')),
    ],
    resolver=list_all_environment_consumption_roles,
)

listEnvironmentGroupInvitationPermissions = gql.QueryField(
    name='listEnvironmentGroupInvitationPermissions',
    type=gql.ArrayType(gql.Ref('Permission')),
    resolver=list_environment_group_invitation_permissions,
)


getPivotRolePresignedUrl = gql.QueryField(
    name='getPivotRolePresignedUrl',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_pivot_role_template,
    test_scope='Environment',
)

getCDKExecPolicyPresignedUrl = gql.QueryField(
    name='getCDKExecPolicyPresignedUrl',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_cdk_exec_policy_template,
    test_scope='Environment',
)


getPivotRoleExternalId = gql.QueryField(
    name='getPivotRoleExternalId',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_external_id,
    test_scope='Environment',
)


getPivotRoleName = gql.QueryField(
    name='getPivotRoleName',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_pivot_role_name,
    test_scope='Environment',
)

getConsumptionRolePolicies = gql.QueryField(
    name='getConsumptionRolePolicies',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='IAMRoleName', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.ArrayType(RoleManagedPolicy),
    resolver=get_consumption_role_policies,
    test_scope='Environment',
)
