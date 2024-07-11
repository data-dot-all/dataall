from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.resolvers import get_redshift_dataset, list_redshift_dataset_tables
from dataall.modules.redshift_datasets.api.datasets.input_types import RedshiftDatasetTableFilter


getRedshiftDataset = gql.QueryField(
    name='getRedshiftDataset',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('RedshiftDataset'),
    resolver=get_redshift_dataset,
)

listRedshiftDatasetTables = gql.QueryField(
    name='listRedshiftDatasetTables',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('filter', RedshiftDatasetTableFilter),
    ],
    type=gql.Ref('RedshiftDatasetTableSearchResult'),
    resolver=list_redshift_dataset_tables,
)
