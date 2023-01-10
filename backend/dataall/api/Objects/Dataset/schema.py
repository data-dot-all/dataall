from ... import gql
from .resolvers import *
from ...constants import DatasetRole, EnvironmentPermission

DatasetStatistics = gql.ObjectType(
    name='DatasetStatistics',
    fields=[
        gql.Field(name='tables', type=gql.Integer),
        gql.Field(name='locations', type=gql.Integer),
        gql.Field(name='upvotes', type=gql.Integer),
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
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='S3BucketName', type=gql.String),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueCrawlerName', type=gql.String),
        gql.Field(name='GlueCrawlerSchedule', type=gql.String),
        gql.Field(name='GlueProfilingJobName', type=gql.String),
        gql.Field(name='GlueProfilingTriggerSchedule', type=gql.String),
        gql.Field(name='IAMDatasetAdminRoleArn', type=gql.String),
        gql.Field(name='KmsAlias', type=gql.String),
        gql.Field(name='bucketCreated', type=gql.Boolean),
        gql.Field(name='glueDatabaseCreated', type=gql.Boolean),
        gql.Field(name='iamAdminRoleCreated', type=gql.Boolean),
        gql.Field(name='lakeformationLocationCreated', type=gql.Boolean),
        gql.Field(name='bucketPolicyCreated', type=gql.Boolean),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='businessOwnerEmail', type=gql.String),
        gql.Field(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Field(name='importedS3Bucket', type=gql.Boolean),
        gql.Field(name='importedGlueDatabase', type=gql.Boolean),
        gql.Field(name='importedKmsKey', type=gql.Boolean),
        gql.Field(name='importedAdminRole', type=gql.Boolean),
        gql.Field(name='imported', type=gql.Boolean),
        gql.Field('lfTagKey', gql.ArrayType(gql.String)),
        gql.Field('lfTagValue', gql.ArrayType(gql.String)),
        gql.Field(
            name='environment',
            type=gql.Ref('Environment'),
            resolver=get_dataset_environment,
        ),
        gql.Field(
            name='organization',
            type=gql.Ref('Organization'),
            resolver=get_dataset_organization,
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
            args=[
                gql.Argument(
                    name='filter', type=gql.Ref('DatasetStorageLocationFilter')
                )
            ],
            resolver=list_locations,
            test_scope='Dataset',
        ),
        gql.Field(
            name='userRoleForDataset',
            type=DatasetRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()
        ),
        gql.Field(
            name='statistics', type=DatasetStatistics, resolver=get_dataset_statistics
        ),
        gql.Field(
            name='shares',
            args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
            type=gql.Ref('ShareSearchResult'),
            resolver=list_dataset_share_objects,
            test_scope='ShareObject',
            test_cases=[
                'anonymous',
                'businessowner',
                'admins',
                'stewards',
                'unauthorized',
            ],
        ),
        gql.Field(
            name='terms',
            resolver=get_dataset_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(
            name='confidentiality', type=gql.Ref('ConfidentialityClassification')
        ),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(
            name='projectPermission',
            args=[
                gql.Argument(name='projectUri', type=gql.NonNullableType(gql.String))
            ],
            type=gql.Ref('DatasetRole'),
        ),
        gql.Field(
            name='redshiftClusterPermission',
            args=[
                gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String))
            ],
            type=gql.Ref('DatasetRole'),
        ),
        gql.Field(
            name='redshiftDataCopyEnabled',
            args=[
                gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String))
            ],
            type=gql.Boolean,
            resolver=resolve_redshift_copy_enabled,
        ),
        gql.Field(
            name='isPublishedInEnvironment',
            args=[
                gql.Argument(
                    name='environmentUri', type=gql.NonNullableType(gql.String)
                )
            ],
            type=gql.Boolean,
        ),
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=get_dataset_stack),
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
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='status', type=gql.String),
    ],
)
