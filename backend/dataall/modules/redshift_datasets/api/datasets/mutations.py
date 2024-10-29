from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.input_types import (
    ImportRedshiftDatasetInput,
    ModifyRedshiftDatasetInput,
)
from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    add_redshift_dataset_tables,
    delete_redshift_dataset,
    delete_redshift_dataset_table,
    import_redshift_dataset,
    update_redshift_dataset,
    update_redshift_dataset_table,
)

importRedshiftDataset = gql.MutationField(
    name='importRedshiftDataset',
    args=[gql.Argument('input', ImportRedshiftDatasetInput)],
    type=gql.Ref('RedshiftDataset'),
    resolver=import_redshift_dataset,
)

updateRedshiftDataset = gql.MutationField(
    name='updateRedshiftDataset',
    args=[
        gql.Argument('datasetUri', gql.String),
        gql.Argument('input', ModifyRedshiftDatasetInput),
    ],
    type=gql.Ref('RedshiftDataset'),
    resolver=update_redshift_dataset,
)

deleteRedshiftDataset = gql.MutationField(
    name='deleteRedshiftDataset',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
    ],
    resolver=delete_redshift_dataset,
    type=gql.Boolean,
)

addRedshiftDatasetTables = gql.MutationField(
    name='addRedshiftDatasetTables',
    args=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument('tables', gql.NonNullableType(gql.ArrayType(gql.String))),
    ],
    type=gql.Ref('RedshiftAddTableResult'),
    resolver=add_redshift_dataset_tables,
)

deleteRedshiftDatasetTable = gql.MutationField(
    name='deleteRedshiftDatasetTable',
    args=[
        gql.Argument('rsTableUri', gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=delete_redshift_dataset_table,
)

updateRedshiftDatasetTable = gql.MutationField(
    name='updateRedshiftDatasetTable',
    args=[
        gql.Argument('rsTableUri', gql.String),
        gql.Argument('input', ModifyRedshiftDatasetInput),
    ],
    type=gql.Ref('RedshiftDatasetTable'),
    resolver=update_redshift_dataset_table,
)
