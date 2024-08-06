from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table.input_types import DatasetTableFilter
from dataall.modules.s3_datasets.api.table.resolvers import get_table, preview, list_table_data_filters
from dataall.modules.s3_datasets.api.table.types import (
    DatasetTable,
    DatasetTableSearchResult,
    DatasetTableDataFilterSearchResult,
)

getDatasetTable = gql.QueryField(
    name='getDatasetTable',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    type=gql.Thunk(lambda: DatasetTable),
    resolver=get_table,
)


listDatasetTables = gql.QueryField(
    name='listDatasetTables',
    args=[gql.Argument(name='filter', type=DatasetTableFilter)],
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

listTableDataFilters = gql.QueryField(
    name='listTableDataFilters',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=DatasetTableFilter),
    ],
    type=DatasetTableDataFilterSearchResult,
    resolver=list_table_data_filters,
)
