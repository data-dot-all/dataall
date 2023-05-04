from dataall.api import gql
from dataall.modules.datasets.api.table.input_types import (
    ModifyDatasetTableInput,
    NewDatasetTableInput,
)
from dataall.modules.datasets.api.table.resolvers import (
    create_table,
    update_table,
    delete_table,
    publish_table_update
)

createDatasetTable = gql.MutationField(
    name='createDatasetTable',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=NewDatasetTableInput),
    ],
    type=gql.Ref('DatasetTable'),
    resolver=create_table,
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

publishDatasetTableUpdate = gql.MutationField(
    name='publishDatasetTableUpdate',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=publish_table_update,
    type=gql.Boolean,
)
