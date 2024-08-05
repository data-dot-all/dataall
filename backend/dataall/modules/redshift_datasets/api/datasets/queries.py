from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    get_redshift_dataset,
    get_redshift_dataset_table,
    list_redshift_schema_dataset_tables,
    list_redshift_dataset_table_columns,
    list_redshift_dataset_tables,
)
from dataall.modules.redshift_datasets.api.datasets.input_types import RedshiftDatasetTableFilter


getRedshiftDataset = gql.QueryField(
    name='getRedshiftDataset',
    args=[gql.Argument('datasetUri', gql.NonNullableType(gql.String))],
    type=gql.Ref('RedshiftDataset'),
    resolver=get_redshift_dataset,
)

listRedshiftDatasetTables = gql.QueryField(
    name='listRedshiftDatasetTables',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument('filter', RedshiftDatasetTableFilter),
    ],
    type=gql.Ref('RedshiftDatasetTableSearchResult'),
    resolver=list_redshift_dataset_tables,
)

getRedshiftDatasetTable = gql.QueryField(
    name='getRedshiftDatasetTable',
    args=[gql.Argument('rsTableUri', gql.NonNullableType(gql.String))],
    type=gql.Ref('RedshiftDatasetTable'),
    resolver=get_redshift_dataset_table,
)

getRedshiftDatasetTableColumns = gql.QueryField(
    name='getRedshiftDatasetTableColumns',
    args=[
        gql.Argument('rsTableUri', gql.NonNullableType(gql.String)),
        gql.Argument('filter', RedshiftDatasetTableFilter),
    ],
    type=gql.Ref('RedshiftDatasetTableColumnSearchResult'),
    resolver=list_redshift_dataset_table_columns,
)

listRedshiftSchemaDatasetTables = gql.QueryField(
    name='listRedshiftSchemaDatasetTables',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
    ],
    type=gql.ArrayType(gql.Ref('RedshiftTable')),
    resolver=list_redshift_schema_dataset_tables,
)
