from dataall.base.api import gql

NewDatasetStorageLocationInput = gql.InputType(
    name='NewDatasetStorageLocationInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('terms', gql.ArrayType(gql.String)),
        gql.Argument('prefix', gql.NonNullableType(gql.String)),
    ],
)

ModifyDatasetFolderInput = gql.InputType(
    name='ModifyDatasetStorageLocationInput',
    arguments=[
        gql.Argument('locationUri', gql.String),
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('terms', gql.ArrayType(gql.String)),
    ],
)

DatasetStorageLocationFilter = gql.InputType(
    name='DatasetStorageLocationFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
