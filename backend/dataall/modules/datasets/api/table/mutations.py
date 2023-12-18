from dataall.base.api import gql
from dataall.modules.datasets.api.table.input_types import ModifyDatasetTableInput
from dataall.modules.datasets.api.table.resolvers import (
    update_table, delete_table, sync_tables,
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
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))
    ],
    type=gql.Ref('DatasetTableSearchResult'),
    resolver=sync_tables,
)
