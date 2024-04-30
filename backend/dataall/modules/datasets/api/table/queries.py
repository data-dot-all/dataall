from dataall.base.api import gql
from dataall.modules.datasets.api.table.input_types import DatasetTableFilter
from dataall.modules.datasets.api.table.resolvers import get_table, preview
from dataall.modules.datasets.api.table.types import (
    DatasetTable,
    DatasetTableSearchResult,
)

getDatasetTable = gql.QueryField(
    name='getDatasetTable',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    type=gql.Thunk(lambda: DatasetTable),
    resolver=get_table,
)


listDatasetTables = gql.QueryField(
    name='listDatasetTables',
    args=[gql.Argument('filter', DatasetTableFilter)],
    type=DatasetTableSearchResult,
    resolver=lambda *_, **__: None,
)


QueryPreviewResult = gql.ObjectType(
    name='QueryPreviewResult',
    fields=[
        gql.Field(name='fields', type=gql.ArrayType(gql.String)),
        gql.Field(name='rows', type=gql.ArrayType(gql.String)),
    ],
)

previewTable = gql.QueryField(
    name='previewTable',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    resolver=preview,
    type=gql.Ref('QueryPreviewResult'),
)
