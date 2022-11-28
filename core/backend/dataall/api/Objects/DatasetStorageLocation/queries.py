from ... import gql
from .resolvers import *

getDatasetStorageLocation = gql.QueryField(
    name='getDatasetStorageLocation',
    args=[gql.Argument(name='locationUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DatasetStorageLocation'),
    resolver=get_storage_location,
)
