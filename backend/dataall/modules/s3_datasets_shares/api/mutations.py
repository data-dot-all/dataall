from dataall.base.api import gql
from dataall.modules.s3_datasets_shares.api.resolvers import (
    verify_dataset_share_objects,
)


verifyDatasetShareObjects = gql.MutationField(
    name='verifyDatasetShareObjects',
    args=[gql.Argument(name='input', type=gql.Ref('ShareObjectSelectorInput'))],
    type=gql.Boolean,
    resolver=verify_dataset_share_objects,
)
