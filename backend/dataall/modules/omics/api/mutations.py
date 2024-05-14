"""The module defines GraphQL mutations for Omics Pipelines"""

from dataall.base.api import gql
from .resolvers import *

createOmicsRun = gql.MutationField(
    name='createOmicsRun',
    type=gql.Ref('OmicsRun'),
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('NewOmicsRunInput')))],
    resolver=create_omics_run,
)

# TODO: need to add the test
deleteOmicsRun = gql.MutationField(
    name='deleteOmicsRun',
    type=gql.Boolean,
    args=[
        gql.Argument(name='runUris', type=gql.NonNullableType(gql.ArrayType(gql.String))),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    resolver=delete_omics_run,
)
