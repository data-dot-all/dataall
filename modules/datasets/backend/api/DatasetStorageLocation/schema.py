from backend.api import gql
from .resolvers import *

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
        gql.Field(name='region', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='S3BucketName', type=gql.String),
        gql.Field(name='S3Prefix', type=gql.String),
        gql.Field(name='locationCreated', type=gql.Boolean),
        gql.Field(name='dataset', type=gql.Ref('Dataset'), resolver=resolve_dataset),
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


DatasetAccessPoint = gql.ObjectType(
    name='DatasetAccessPoint',
    fields=[
        gql.Field(name='accessPointUri', type=gql.ID),
        gql.Field(name='location', type=DatasetStorageLocation),
        gql.Field(name='dataset', type=gql.Ref('Dataset')),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='S3BucketName', type=gql.String),
        gql.Field(name='S3Prefix', type=gql.String),
        gql.Field(name='S3AccessPointName', type=gql.String),
    ],
)


DatasetAccessPointSearchResult = gql.ObjectType(
    name='DatasetAccessPointSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Integer),
        gql.Field(name='hasPrevious', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(DatasetAccessPoint)),
    ],
)
