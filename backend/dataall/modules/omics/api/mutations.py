"""The module defines GraphQL mutations for Omics Pipelines"""

from dataall.base.api import gql
from .resolvers import *

createOmicsRun = gql.MutationField(
    name="createOmicsRun",
    type=gql.Ref("OmicsRun"),
    args=[gql.Argument(name="input", type=gql.NonNullableType(gql.Ref("NewOmicsRunInput")))],
    resolver=create_omics_run,
)
# TODO implement updates to runs!
# updateOmicsRun = gql.MutationField(
#     name="updateOmicsRun",
#     type=gql.Ref("OmicsRun"),
#     args=[
#         gql.Argument(name="OmicsRunUri", type=gql.NonNullableType(gql.String)),
#         gql.Argument(name="input", type=gql.Ref("UpdateOmicsRunInput")),
#     ],
#     resolver=update_omics_pipeline,
# )

# TODO: not used in the frontend at the moment
# deleteOmicsRun = gql.MutationField(
#     name="deleteOmicsRun",
#     type=gql.Boolean,
#     args=[
#         gql.Argument(name="runUri", type=gql.NonNullableType(gql.String)),
#         gql.Argument(name="deleteFromAWS", type=gql.Boolean),
#     ],
#     resolver=delete_omics_run,
# )


