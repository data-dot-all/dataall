from dataall.base.api import gql
from dataall.modules.shares_base.services.shares_enums import (
    ShareableType,
    PrincipalType,
    ShareItemHealthStatus,
    ShareObjectDataPermission,
)
from dataall.modules.shares_base.api.resolvers import (
    resolve_dataset,
    resolve_existing_shared_items,
    resolve_share_object_statistics,
    resolve_principal,
    resolve_group,
    list_shareable_objects,
    resolve_user_role,
    resolve_can_view_logs,
)
from dataall.core.environment.api.resolvers import resolve_environment

ShareItem = gql.ObjectType(
    name='ShareItem',
    fields=[
        gql.Field(name='shareUri', type=gql.String),
        gql.Field(name='shareItemUri', type=gql.ID),
        gql.Field('itemUri', gql.String),
        gql.Field(name='status', type=gql.Ref('ShareItemStatus')),
        gql.Field(name='action', type=gql.String),
        gql.Field('itemType', ShareableType.toGraphQLEnum()),
        gql.Field('itemName', gql.String),
        gql.Field('description', gql.String),
        gql.Field('healthStatus', ShareItemHealthStatus.toGraphQLEnum()),
        gql.Field('healthMessage', gql.String),
        gql.Field('lastVerificationTime', gql.String),
        gql.Field('attachedDataFilterUri', gql.String),
    ],
)

ShareObjectItemDataFilter = gql.ObjectType(
    name='ShareObjectItemDataFilter',
    fields=[
        gql.Field(name='attachedDataFilterUri', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='dataFilterUris', type=gql.ArrayType(gql.String)),
        gql.Field(name='dataFilterNames', type=gql.ArrayType(gql.String)),
        gql.Field(name='itemUri', type=gql.String),
    ],
)


NotSharedItem = gql.ObjectType(
    name='NotSharedItem',
    fields=[
        gql.Field('itemUri', gql.String),
        gql.Field('shareItemUri', gql.String),
        gql.Field('itemType', ShareableType.toGraphQLEnum()),
        gql.Field('label', gql.String),
        gql.Field('tags', gql.ArrayType(gql.String)),
        gql.Field('created', gql.String),
    ],
)

NotSharedItemsSearchResult = gql.ObjectType(
    name='NotSharedItemsSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(NotSharedItem)),
    ],
)

SharedItemSearchResult = gql.ObjectType(
    name='SharedItemSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('ShareItem'))),
    ],
)

ShareObjectStatistic = gql.ObjectType(
    name='ShareObjectStatistic',
    fields=[
        gql.Field(name='sharedItems', type=gql.Integer),
        gql.Field(name='revokedItems', type=gql.Integer),
        gql.Field(name='failedItems', type=gql.Integer),
        gql.Field(name='pendingItems', type=gql.Integer),
    ],
)

DatasetLink = gql.ObjectType(
    name='DatasetLink',
    fields=[
        gql.Field(name='datasetUri', type=gql.String),
        gql.Field(name='datasetName', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='environmentName', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='exists', type=gql.Boolean),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='datasetType', type=gql.String),
        gql.Field(name='enableExpiration', type=gql.Boolean),
        gql.Field(name='expirySetting', type=gql.String),
    ],
)

ShareObject = gql.ObjectType(
    name='ShareObject',
    fields=[
        gql.Field(name='shareUri', type=gql.ID),
        gql.Field(name='status', type=gql.Ref('ShareObjectStatus')),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='deleted', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='datasetUri', type=gql.String),
        gql.Field(name='requestPurpose', type=gql.String),
        gql.Field(name='rejectPurpose', type=gql.String),
        gql.Field(name='expiryDate', type=gql.String),
        gql.Field(name='requestedExpiryDate', type=gql.String),
        gql.Field(name='submittedForExtension', type=gql.Boolean),
        gql.Field(name='extensionReason', type=gql.String),
        gql.Field(name='lastExtensionDate', type=gql.String),
        gql.Field(name='nonExpirable', type=gql.Boolean),
        gql.Field(name='shareExpirationPeriod', type=gql.Integer),
        gql.Field(name='dataset', type=DatasetLink, resolver=resolve_dataset),
        gql.Field(name='alreadyExisted', type=gql.Boolean),
        gql.Field(name='existingSharedItems', type=gql.Boolean, resolver=resolve_existing_shared_items),
        gql.Field(
            name='statistics',
            type=gql.Ref('ShareObjectStatistic'),
            resolver=resolve_share_object_statistics,
        ),
        gql.Field(name='principal', resolver=resolve_principal, type=gql.Ref('Principal')),
        gql.Field(
            name='environment',
            resolver=resolve_environment,
            type=gql.Ref('Environment'),
        ),
        gql.Field(
            name='group',
            resolver=resolve_group,
            type=gql.String,
        ),
        gql.Field(
            'items',
            args=[gql.Argument(name='filter', type=gql.Ref('ShareableObjectFilter'))],
            type=gql.Ref('SharedItemSearchResult'),
            resolver=list_shareable_objects,
        ),
        gql.Field(
            name='canViewLogs',
            resolver=resolve_can_view_logs,
            type=gql.Boolean,
        ),
        gql.Field(
            name='userRoleForShareObject',
            type=gql.Ref('ShareObjectPermission'),
            resolver=resolve_user_role,
        ),
        gql.Field('permissions', gql.ArrayType(ShareObjectDataPermission.toGraphQLEnum())),
    ],
)

ShareSearchResult = gql.ObjectType(
    name='ShareSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('ShareObject'))),
    ],
)

EnvironmentPublishedItem = gql.ObjectType(
    name='EnvironmentPublishedItem',
    fields=[
        gql.Field(name='shareUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='datasetName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='itemType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='itemName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='targetEnvironmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='created', type=gql.NonNullableType(gql.String)),
    ],
)

EnvironmentPublishedItemSearchResults = gql.ObjectType(
    name='EnvironmentPublishedItemSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(EnvironmentPublishedItem)),
    ],
)

Principal = gql.ObjectType(
    name='Principal',
    fields=[
        gql.Field(name='principalName', type=gql.String),
        gql.Field(name='principalType', type=PrincipalType.toGraphQLEnum()),
        gql.Field(name='principalId', type=gql.ID),
        gql.Field(name='principalRoleName', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='environmentName', type=gql.String),
    ],
)

PrincipalSearchResult = gql.ObjectType(
    name='PrincipalSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(Principal)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)

ShareLog = gql.ObjectType(
    name='ShareLog',
    fields=[
        gql.Field(name='logStream', type=gql.String),
        gql.Field(name='logGroup', type=gql.String),
        gql.Field(name='timestamp', type=gql.String),
        gql.Field(name='message', type=gql.String),
    ],
)
