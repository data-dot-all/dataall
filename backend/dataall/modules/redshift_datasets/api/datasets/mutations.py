from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.datasets.input_types import (
    ImportRedshiftDatasetInput,
)
from dataall.modules.redshift_datasets.api.datasets.resolvers import import_redshift_dataset

importRedshiftDataset = gql.MutationField(
    name='importRedshiftDataset',
    args=[gql.Argument(name='input', type=ImportRedshiftDatasetInput)],
    type=gql.Ref('RedshiftDataset'),
    resolver=import_redshift_dataset,
)
