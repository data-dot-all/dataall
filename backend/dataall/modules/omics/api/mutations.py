"""The module defines GraphQL mutations for Omics Pipelines"""

from dataall.base.api import gql
from .resolvers import create_omics_run, delete_omics_run
from .types import OmicsRun
from .input_types import NewOmicsRunInput, OmicsDeleteInput

createOmicsRun = gql.MutationField(
    name='createOmicsRun',
    type=OmicsRun,
    args=[gql.Argument(name='input', type=gql.NonNullableType(NewOmicsRunInput))],
    resolver=create_omics_run,
)

deleteOmicsRun = gql.MutationField(
    name='deleteOmicsRun',
    type=gql.Boolean,
    args=[gql.Argument(name='input', type=gql.NonNullableType(OmicsDeleteInput))],
    resolver=delete_omics_run,
)
