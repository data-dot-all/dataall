from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table.input_types import ModifyDatasetTableInput, NewTableDataFilterInput
from dataall.modules.s3_datasets.api.table.resolvers import (
    update_table,
    delete_table,
    sync_tables,
    create_table_data_filter,
    delete_table_data_filter,
)

updateDatasetTable = gql.MutationField(
    name='updateDatasetTable',
    args=[
        gql.Argument(name='tableUri', type=gql.String),
        gql.Argument(name='input', type=ModifyDatasetTableInput),
    ],
    type=gql.Ref('DatasetTable'),
    resolver=update_table,
)

deleteDatasetTable = gql.MutationField(
    name='deleteDatasetTable',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=delete_table,
)

syncTables = gql.MutationField(
    name='syncTables',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Integer,
    resolver=sync_tables,
)

createTableDataFilter = gql.MutationField(
    name='createTableDataFilter',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.NonNullableType(NewTableDataFilterInput)),
    ],
    type=gql.Ref('DatasetTableDataFilter'),
    resolver=create_table_data_filter,
)

deleteTableDataFilter = gql.MutationField(
    name='deleteTableDataFilter',
    args=[gql.Argument(name='filterUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=delete_table_data_filter,
)
