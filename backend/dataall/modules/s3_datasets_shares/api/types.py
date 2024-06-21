from dataall.base.api import gql
from dataall.modules.s3_datasets_shares.api.resolvers import resolve_shared_db_name


S3ConsumptionData = gql.ObjectType(
    name='S3ConsumptionData',
    fields=[
        gql.Field(name='s3AccessPointName', type=gql.String),
        gql.Field(name='sharedGlueDatabase', type=gql.String),
        gql.Field(name='s3bucketName', type=gql.String),
    ],
)

SharedDatabaseTableItem = gql.ObjectType(
    name='SharedDatabaseTableItem',
    fields=[
        gql.Field(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='GlueDatabaseName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='shareUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='targetEnvAwsAccountId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='targetEnvRegion', type=gql.NonNullableType(gql.String)),
        gql.Field(name='sharedGlueDatabaseName', type=gql.NonNullableType(gql.String), resolver=resolve_shared_db_name),
    ],
)
