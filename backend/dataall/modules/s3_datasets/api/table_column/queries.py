from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table_column.resolvers import list_table_columns

listDatasetTableColumns = gql.QueryField(
    name='listDatasetTableColumns',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetTableColumnFilter')),
    ],
    type=gql.Ref('DatasetTableColumnSearchResult'),
    resolver=list_table_columns,
)
