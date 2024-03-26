from dataall.base.api import gql
from dataall.modules.s3_datasets.api.dataset.resolvers import (
    get_dataset,
    get_dataset_assume_role_url,
    get_file_upload_presigned_url
)

getDataset = gql.QueryField(
    name='getDataset',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Dataset'),
    resolver=get_dataset,
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

# TODO: MOVE THIS ITEM TO DATASHARING MODULE
# listShareObjects = gql.QueryField(
#     name='listDatasetShareObjects',
#     resolver=list_dataset_share_objects,
#     args=[
#         gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
#         gql.Argument(name='environmentUri', type=gql.String),
#         gql.Argument(name='page', type=gql.Integer),
#     ],
#     type=gql.Ref('ShareSearchResult'),
# )
