"""The module defines GraphQL mutations for Omics Pipelines"""

from dataall.base.api import gql
from .resolvers import *

createOmicsRun = gql.MutationField(
    name='createOmicsRun',
    type=gql.Ref('OmicsRun'),
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('NewOmicsRunInput')))],
    resolver=create_omics_run,
)

deleteOmicsRun = gql.MutationField(
    name='deleteOmicsRun',
    type=gql.Boolean,
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('OmicsDeleteInput')))],
    resolver=delete_omics_run,
)
