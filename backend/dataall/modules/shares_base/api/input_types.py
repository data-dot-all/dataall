from dataall.base.api.constants import SortDirection, gql
from dataall.modules.shares_base.services.shares_enums import ShareableType, ShareSortField, ShareObjectDataPermission

NewShareObjectInput = gql.InputType(
    name='NewShareObjectInput',
    arguments=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='principalRoleName', type=gql.String),
        gql.Argument(name='principalType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='requestPurpose', type=gql.String),
        gql.Argument(name='attachMissingPolicies', type=gql.Boolean),
        gql.Argument(
            name='permissions', type=gql.NonNullableType(gql.ArrayType(ShareObjectDataPermission.toGraphQLEnum()))
        ),
        gql.Argument(name='shareExpirationPeriod', type=gql.Integer),
        gql.Argument(name='nonExpirable', type=gql.Boolean),
    ],
)

AddSharedItemInput = gql.InputType(
    name='AddSharedItemInput',
    arguments=[
        gql.Argument(name='itemUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='itemType', type=gql.NonNullableType(ShareableType.toGraphQLEnum())),
    ],
)

ShareItemSelectorInput = gql.InputType(
    name='ShareItemSelectorInput',
    arguments=[
        gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='itemUris', type=gql.NonNullableType(gql.ArrayType(gql.String))),
    ],
)

ShareSortCriteria = gql.InputType(
    name='ShareSortCriteria',
    arguments=[
        gql.Argument(name='field', type=gql.NonNullableType(ShareSortField.toGraphQLEnum())),
        gql.Argument(name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())),
    ],
)

ShareObjectFilter = gql.InputType(
    name='ShareObjectFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('sort', gql.ArrayType(ShareSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('status', gql.ArrayType(gql.String)),
        gql.Argument('dataset_owners', gql.ArrayType(gql.String)),
        gql.Argument('datasets_uris', gql.ArrayType(gql.String)),
        gql.Argument('share_requesters', gql.ArrayType(gql.String)),
        gql.Argument('share_iam_roles', gql.ArrayType(gql.String)),
    ],
)

ShareableObjectFilter = gql.InputType(
    name='ShareableObjectFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument(name='isShared', type=gql.Boolean),
        gql.Argument(name='isRevokable', type=gql.Boolean),
        gql.Argument(name='isHealthy', type=gql.Boolean),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)

EnvironmentDataItemFilter = gql.InputType(
    name='EnvironmentDataItemFilter',
    arguments=[
        gql.Argument('itemTypes', gql.ArrayType(gql.String)),
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('uniqueShares', gql.Boolean),
    ],
)

PrincipalFilter = gql.InputType(
    name='PrincipalFilter',
    arguments=[
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument(name='principalType', type=gql.Ref('PrincipalType')),
        gql.Argument(name='term', type=gql.String),
    ],
)

ModifyFiltersTableShareItemInput = gql.InputType(
    name='ModifyFiltersTableShareItemInput',
    arguments=[
        gql.Argument(name='shareItemUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filterUris', type=gql.ArrayType(gql.String)),
        gql.Argument(name='filterNames', type=gql.ArrayType(gql.String)),
    ],
)
