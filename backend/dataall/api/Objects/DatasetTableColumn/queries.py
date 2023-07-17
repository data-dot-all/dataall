from ... import gql
from .resolvers import *

listDatasetTableColumns = gql.QueryField(
    name='listDatasetTableColumns',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetTableColumnFilter')),
    ],
    type=gql.Ref('DatasetTableColumnSearchResult'),
    resolver=list_table_columns,
)
