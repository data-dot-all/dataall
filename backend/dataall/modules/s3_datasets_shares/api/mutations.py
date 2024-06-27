from dataall.base.api import gql
from dataall.modules.s3_datasets_shares.api.resolvers import (
    verify_dataset_share_objects,
    reapply_share_items_share_object_for_dataset,
)


verifyDatasetShareObjects = gql.MutationField(
    name='verifyDatasetShareObjects',
    args=[gql.Argument(name='input', type=gql.Ref('ShareObjectSelectorInput'))],
    type=gql.Boolean,
    resolver=verify_dataset_share_objects,
)

reApplyShareObjectItemsOnDataset = gql.MutationField(
    name='reApplyShareObjectItemsOnDataset',
    args=[gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=reapply_share_items_share_object_for_dataset,
)
