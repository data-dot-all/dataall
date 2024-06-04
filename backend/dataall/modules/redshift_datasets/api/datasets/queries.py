from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    get_redshift_dataset,
)


getRedshiftDataset = gql.QueryField(
    name='getRedshiftDataset',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('RedshiftDataset'),
    resolver=get_redshift_dataset,
)
