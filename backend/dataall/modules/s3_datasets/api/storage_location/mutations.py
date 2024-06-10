from dataall.base.api import gql
from dataall.modules.s3_datasets.api.storage_location.input_types import (
    ModifyDatasetFolderInput,
    NewDatasetStorageLocationInput,
)
from dataall.modules.s3_datasets.api.storage_location.resolvers import (
    create_storage_location,
    update_storage_location,
    remove_storage_location,
)
from dataall.modules.s3_datasets.api.storage_location.types import DatasetStorageLocation

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
