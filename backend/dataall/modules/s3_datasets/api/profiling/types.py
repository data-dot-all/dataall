from dataall.base.api import gql
from dataall.modules.s3_datasets.api.profiling.resolvers import (
    resolve_dataset,
    resolve_profiling_run_status,
    resolve_profiling_results,
)

DatasetProfilingRun = gql.ObjectType(
    name='DatasetProfilingRun',
    fields=[
        gql.Field(name='profilingRunUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='GlueJobName', type=gql.String),
        gql.Field(name='GlueJobRunId', type=gql.String),
        gql.Field(name='GlueTriggerSchedule', type=gql.String),
        gql.Field(name='GlueTriggerName', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='results', type=gql.String, resolver=resolve_profiling_results),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field('status', type=gql.String, resolver=resolve_profiling_run_status),
        gql.Field(name='dataset', type=gql.Ref('Dataset'), resolver=resolve_dataset),
    ],
)

DatasetProfilingRunSearchResults = gql.ObjectType(
    name='DatasetProfilingRunSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DatasetProfilingRun)),
    ],
)
