from dataall.base.api import gql
from dataall.modules.s3_datasets.api.storage_location.resolvers import get_storage_location

getDatasetStorageLocation = gql.QueryField(
    name='getDatasetStorageLocation',
    args=[gql.Argument(name='locationUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DatasetStorageLocation'),
    resolver=get_storage_location,
)
