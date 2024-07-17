from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.input_types import (
    ImportRedshiftDatasetInput,
)
from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    add_redshift_dataset_tables,
    delete_redshift_dataset_table,
    import_redshift_dataset,
)

importRedshiftDataset = gql.MutationField(
    name='importRedshiftDataset',
    args=[gql.Argument(name='input', type=ImportRedshiftDatasetInput)],
    type=gql.Ref('RedshiftDataset'),
    resolver=import_redshift_dataset,
)

addRedshiftDatasetTables = gql.MutationField(
    name='addRedshiftDatasetTables',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument(name='tables', type=gql.NonNullableType(gql.ArrayType(gql.String))),
    ],
    type=gql.Boolean,
    resolver=add_redshift_dataset_tables,
)

deleteRedshiftDatasetTable = gql.MutationField(
    name='deleteRedshiftDatasetTable',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument(name='rsTableUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=delete_redshift_dataset_table,
)
