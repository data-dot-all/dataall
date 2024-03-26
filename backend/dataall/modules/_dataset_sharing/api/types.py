from dataall.base.api import gql
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (
    ShareableType,
    PrincipalType,
    ShareItemHealthStatus,
)
from dataall.modules.dataset_sharing.api.resolvers import (
    union_resolver,
    resolve_shared_item,
    resolve_dataset,
    resolve_consumption_data,
    resolve_existing_shared_items,
    resolve_share_object_statistics,
    resolve_principal,
    resolve_group,
    list_shareable_objects,
    resolve_user_role,
    resolve_shared_database_name,
)
from dataall.core.environment.api.resolvers import resolve_environment

ShareableObject = gql.Union(
    name='ShareableObject',
    types=[gql.Ref('DatasetTable'), gql.Ref('DatasetStorageLocation')],
    resolver=union_resolver,
)


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
        gql.Field(
            name='sharedObject',
            type=gql.Ref('ShareableObject'),
            resolver=resolve_shared_item,
        ),
        # gql.Field(name="permission", type=gql.String)
    ],
)

NotSharedItem = gql.ObjectType(
    name='NotSharedItem',
    fields=[
        gql.Field('itemUri', gql.String),
        gql.Field('shareItemUri', gql.String),
        gql.Field('itemType', ShareableType.toGraphQLEnum()),
        gql.Field('label', gql.String),
        # gql.Field("permission", DatasetRole.toGraphQLEnum()),
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
        gql.Field(name='locations', type=gql.Integer),
        gql.Field(name='tables', type=gql.Integer),
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
    ],
)

ConsumptionData = gql.ObjectType(
    name='ConsumptionData',
    fields=[
        gql.Field(name='s3AccessPointName', type=gql.String),
        gql.Field(name='sharedGlueDatabase', type=gql.String),
        gql.Field(name='s3bucketName', type=gql.String),
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
        gql.Field(name='dataset', type=DatasetLink, resolver=resolve_dataset),
        gql.Field(name='consumptionData', type=gql.Ref('ConsumptionData'), resolver=resolve_consumption_data),
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
            name='userRoleForShareObject',
            type=gql.Ref('ShareObjectPermission'),
            resolver=resolve_user_role,
        ),
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
        gql.Field(name='itemAccess', type=gql.NonNullableType(gql.String)),
        gql.Field(name='itemType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='created', type=gql.NonNullableType(gql.String)),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
        gql.Field(name='S3AccessPointName', type=gql.String),
        gql.Field(
            'sharedGlueDatabaseName',
            type=gql.String,
            resolver=resolve_shared_database_name,
        ),
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
        gql.Field(name='principalId', type=gql.ID),
        gql.Field(name='principalType', type=PrincipalType.toGraphQLEnum()),
        gql.Field(name='principalName', type=gql.String),
        gql.Field(name='principalIAMRoleName', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='environmentName', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='organizationName', type=gql.String),
        gql.Field(name='organizationUri', type=gql.String),
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
