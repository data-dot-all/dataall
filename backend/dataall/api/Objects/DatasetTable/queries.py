from ... import gql
from .input_types import DatasetTableFilter
from .resolvers import *
from .schema import (
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

previewTable2 = gql.QueryField(
    name='previewTable2',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    resolver=preview,
    type=gql.Ref('QueryPreviewResult'),
)

getSharedDatasetTables = gql.QueryField(
    name='getSharedDatasetTables',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='envUri', type=gql.NonNullableType(gql.String))
    ],
    type=gql.ArrayType(gql.Ref('SharedDatasetTableItem')),
    resolver=list_shared_tables_by_env_dataset,
)
