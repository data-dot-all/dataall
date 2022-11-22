from .resolvers import *

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
        gql.Field(name='status', type=gql.Ref('ShareObjectStatus')),
        gql.Field(name='action', type=gql.String),
        gql.Field('itemType', ShareableType.toGraphQLEnum()),
        gql.Field('itemName', gql.String),
        gql.Field('description', gql.String),
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
    ],
)

DatasetLink = gql.ObjectType(
    name='DatasetLink',
    fields=[
        gql.Field(name='datasetUri', type=gql.String),
        gql.Field(name='datasetName', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='environmentName', type=gql.String),
        gql.Field(name='exists', type=gql.Boolean),
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
        gql.Field(name='dataset', type=DatasetLink, resolver=resolve_dataset),
        gql.Field(name='statistics', type=gql.Ref('ShareObjectStatistic')),
        gql.Field(
            name='principal', resolver=resolve_principal, type=gql.Ref('Principal')
        ),
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
