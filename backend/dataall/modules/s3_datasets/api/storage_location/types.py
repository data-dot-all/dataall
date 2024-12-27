from dataall.base.api import gql
from dataall.modules.s3_datasets.api.storage_location.resolvers import (
    resolve_glossary_terms,
    resolve_dataset,
    get_folder_restricted_information,
)

DatasetStorageLocation = gql.ObjectType(
    name='DatasetStorageLocation',
    fields=[
        gql.Field(name='locationUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='S3Prefix', type=gql.String),
        gql.Field(name='locationCreated', type=gql.Boolean),
        gql.Field(name='dataset', type=gql.Ref('Dataset'), resolver=resolve_dataset),
        gql.Field(
            name='restricted',
            type=gql.Ref('DatasetRestrictedInformation'),
            resolver=get_folder_restricted_information,
        ),
        gql.Field(name='userRoleForStorageLocation', type=gql.Ref('DatasetRole')),
        gql.Field(name='environmentEndPoint', type=gql.String),
        gql.Field(
            name='terms',
            type=gql.Ref('TermSearchResult'),
            resolver=resolve_glossary_terms,
        ),
    ],
)


DatasetStorageLocationSearchResult = gql.ObjectType(
    name='DatasetStorageLocationSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(DatasetStorageLocation)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
