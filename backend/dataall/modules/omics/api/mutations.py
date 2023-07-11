"""The module defines GraphQL mutations for Omics Pipelines"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql
from .resolvers import *

createOmicsRun = gql.MutationField(
    name="createOmicsRun",
    type=gql.Ref("OmicsRun"),
    args=[gql.Argument(name="input", type=gql.NonNullableType(gql.Ref("NewOmicsRunInput")))],
    resolver=create_omics_run,
)

# updateOmicsPipeline = gql.MutationField(
#     name="updateOmicsPipeline",
#     type=gql.Ref("OmicsPipeline"),
#     args=[
#         gql.Argument(name="OmicsPipelineUri", type=gql.NonNullableType(gql.String)),
#         gql.Argument(name="input", type=gql.Ref("UpdateOmicsPipelineInput")),
#     ],
#     resolver=update_omics_pipeline,
# )

deleteOmicsRun = gql.MutationField(
    name="deleteOmicsRun",
    type=gql.Boolean,
    args=[
        gql.Argument(name="runUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="deleteFromAWS", type=gql.Boolean),
    ],
    resolver=delete_omics_run,
)


