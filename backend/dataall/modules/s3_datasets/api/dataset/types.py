from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.s3_datasets.api.dataset.resolvers import (
    get_dataset_environment_simplified,
    get_dataset_owners_group,
    get_dataset_stewards_group,
    list_tables,
    list_locations,
    resolve_user_role,
    get_dataset_statistics,
    get_dataset_glossary_terms,
    resolve_dataset_stack,
    get_dataset_restricted_information,
)
from dataall.core.environment.api.enums import EnvironmentPermission

DatasetStatistics = gql.ObjectType(
    name='DatasetStatistics',
    fields=[
        gql.Field(name='tables', type=gql.Integer),
        gql.Field(name='locations', type=gql.Integer),
        gql.Field(name='upvotes', type=gql.Integer),
    ],
)

DatasetRestrictedInformation = gql.ObjectType(
    name='DatasetRestrictedInformation',
    fields=[
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='S3BucketName', type=gql.String),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueCrawlerName', type=gql.String),
        gql.Field(name='IAMDatasetAdminRoleArn', type=gql.String),
        gql.Field(name='KmsAlias', type=gql.String),
        gql.Field(name='importedS3Bucket', type=gql.Boolean),
        gql.Field(name='importedGlueDatabase', type=gql.Boolean),
        gql.Field(name='importedKmsKey', type=gql.Boolean),
        gql.Field(name='importedAdminRole', type=gql.Boolean),
    ],
)

Dataset = gql.ObjectType(
    name='Dataset',
    fields=[
        gql.Field(name='datasetUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='admins', type=gql.ArrayType(gql.String)),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='imported', type=gql.Boolean),
        gql.Field(
            name='restricted',
            type=DatasetRestrictedInformation,
            resolver=get_dataset_restricted_information,
        ),
        gql.Field(
            name='environment',
            type=gql.Ref('EnvironmentSimplified'),
            resolver=get_dataset_environment_simplified,
        ),
        gql.Field(
            name='owners',
            type=gql.String,
            resolver=get_dataset_owners_group,
        ),
        gql.Field(
            name='stewards',
            type=gql.String,
            resolver=get_dataset_stewards_group,
        ),
        gql.Field(
            name='tables',
            type=gql.Ref('DatasetTableSearchResult'),
            args=[gql.Argument(name='filter', type=gql.Ref('DatasetTableFilter'))],
            resolver=list_tables,
            test_scope='Dataset',
        ),
        gql.Field(
            name='locations',
            type=gql.Ref('DatasetStorageLocationSearchResult'),
            args=[gql.Argument(name='filter', type=gql.Ref('DatasetStorageLocationFilter'))],
            resolver=list_locations,
            test_scope='Dataset',
        ),
        gql.Field(
            name='userRoleForDataset',
            type=DatasetRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()),
        gql.Field(name='statistics', type=DatasetStatistics, resolver=get_dataset_statistics),
        gql.Field(
            name='terms',
            resolver=get_dataset_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(name='confidentiality', type=gql.String),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=resolve_dataset_stack),
        gql.Field(name='autoApprovalEnabled', type=gql.Boolean),
        gql.Field(name='enableExpiration', type=gql.Boolean),
        gql.Field(name='expirySetting', type=gql.String),
        gql.Field(name='expiryMinDuration', type=gql.Integer),
        gql.Field(name='expiryMaxDuration', type=gql.Integer),
    ],
)

DatasetSearchResult = gql.ObjectType(
    name='DatasetSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(Dataset)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)

GlueCrawler = gql.ObjectType(
    name='GlueCrawler',
    fields=[
        gql.Field(name='Name', type=gql.ID),
        gql.Field(name='status', type=gql.String),
    ],
)
