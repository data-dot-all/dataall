from dataall.api import gql
from dataall.modules.datasets.api.DatasetStorageLocation.input_types import (
    ModifyDatasetFolderInput,
    NewDatasetStorageLocationInput,
)
from dataall.modules.datasets.api.DatasetStorageLocation.resolvers import (
    create_storage_location,
    update_storage_location,
    remove_storage_location,
    publish_location_update
)
from dataall.modules.datasets.api.DatasetStorageLocation.schema import DatasetStorageLocation

createDatasetStorageLocation = gql.MutationField(
    name='createDatasetStorageLocation',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=NewDatasetStorageLocationInput),
    ],
    type=gql.Thunk(lambda: DatasetStorageLocation),
    resolver=create_storage_location,
)

updateDatasetStorageLocation = gql.MutationField(
    name='updateDatasetStorageLocation',
    args=[
        gql.Argument(name='locationUri', type=gql.String),
        gql.Argument(name='input', type=ModifyDatasetFolderInput),
    ],
    type=gql.Thunk(lambda: DatasetStorageLocation),
    resolver=update_storage_location,
)


deleteDatasetStorageLocation = gql.MutationField(
    name='deleteDatasetStorageLocation',
    args=[gql.Argument(name='locationUri', type=gql.NonNullableType(gql.String))],
    resolver=remove_storage_location,
    type=gql.Boolean,
)

publishDatasetStorageLocationUpdate = gql.MutationField(
    name='publishDatasetStorageLocationUpdate',
    args=[
        gql.Argument(name='locationUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=publish_location_update,
    type=gql.Boolean,
)
