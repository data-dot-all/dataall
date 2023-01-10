from .input_types import EnvironmentFilter
from .resolvers import *

from .schema import Environment, EnvironmentSearchResult


getTrustAccount = gql.QueryField(
    name='getTrustAccount',
    type=gql.String,
    resolver=get_trust_account,
    test_scope='Environment',
)

checkEnvironment = gql.QueryField(
    name='checkEnvironment',
    args=[gql.Argument(name='input', type=gql.Ref('AwsEnvironmentInput'))],
    type=gql.String,
    resolver=check_environment,
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


listDatasetsCreatedInEnvironment = gql.QueryField(
    name='listDatasetsCreatedInEnvironment',
    type=gql.Ref('DatasetSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetFilter')),
    ],
    resolver=list_datasets_created_in_environment,
    test_scope='Dataset',
)


searchEnvironmentDataItems = gql.QueryField(
    name='searchEnvironmentDataItems',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('EnvironmentDataItemFilter')),
    ],
    resolver=list_shared_with_environment_data_items,
    type=gql.Ref('EnvironmentPublishedItemSearchResults'),
    test_scope='Dataset',
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

listEnvironmentRedshiftClusters = gql.QueryField(
    name='listEnvironmentClusters',
    type=gql.Ref('RedshiftClusterSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('RedshiftClusterFilter')),
    ],
    resolver=list_environment_redshift_clusters,
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

listEnvironmentGroupInvitationPermissions = gql.QueryField(
    name='listEnvironmentGroupInvitationPermissions',
    args=[
        gql.Argument(name='environmentUri', type=gql.String),
    ],
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
