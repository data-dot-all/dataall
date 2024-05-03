from dataall.base.api import gql
from dataall.modules.datasets.api.dataset.input_types import DatasetFilter
from dataall.modules.datasets.api.dataset.resolvers import (
    get_dataset,
    list_all_user_datasets,
    list_owned_datasets,
    get_dataset_assume_role_url,
    get_file_upload_presigned_url,
    list_datasets_owned_by_env_group,
    list_datasets_created_in_environment,
)
from dataall.modules.datasets.api.dataset.types import DatasetSearchResult

getDataset = gql.QueryField(
    name='getDataset',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Dataset'),
    resolver=get_dataset,
    test_scope='Dataset',
)


listDatasets = gql.QueryField(
    name='listDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetSearchResult,
    resolver=list_all_user_datasets,
    test_scope='Dataset',
)

listOwnedDatasets = gql.QueryField(
    name='listOwnedDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetSearchResult,
    resolver=list_owned_datasets,
    test_scope='Dataset',
)


getDatasetAssumeRoleUrl = gql.QueryField(
    name='getDatasetAssumeRoleUrl',
    args=[gql.Argument(name='datasetUri', type=gql.String)],
    type=gql.String,
    resolver=get_dataset_assume_role_url,
    test_scope='Dataset',
)


getDatasetPresignedUrl = gql.QueryField(
    name='getDatasetPresignedUrl',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('DatasetPresignedUrlInput')),
    ],
    type=gql.String,
    resolver=get_file_upload_presigned_url,
)

listDatasetsOwnedByEnvGroup = gql.QueryField(
    name='listDatasetsOwnedByEnvGroup',
    type=gql.Ref('DatasetSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetFilter')),
    ],
    resolver=list_datasets_owned_by_env_group,
    test_scope='Dataset',
)

listDatasetsCreatedInEnvironment = gql.QueryField(
    name='listDatasetsCreatedInEnvironment',
    type=gql.Ref('DatasetSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetFilter')),
    ],
    resolver=list_datasets_created_in_environment,
    test_scope='Dataset',
)
