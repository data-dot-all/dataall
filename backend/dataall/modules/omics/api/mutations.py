"""The module defines GraphQL mutations for Omics Pipelines"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql
from .resolvers import *

createOmicsPipeline = gql.MutationField(
    name="createOmicsPipeline",
    type=gql.Ref("OmicsPipeline"),
    args=[gql.Argument(name="input", type=gql.NonNullableType(gql.Ref("NewOmicsPipelineInput")))],
    resolver=create_omics_pipeline,
)

updateOmicsPipeline = gql.MutationField(
    name="updateOmicsPipeline",
    type=gql.Ref("OmicsPipeline"),
    args=[
        gql.Argument(name="OmicsPipelineUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="input", type=gql.Ref("UpdateOmicsPipelineInput")),
    ],
    resolver=update_omics_pipeline,
)

deleteOmicsPipeline = gql.MutationField(
    name="deleteOmicsPipeline",
    type=gql.Boolean,
    args=[
        gql.Argument(name="OmicsPipelineUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="deleteFromAWS", type=gql.Boolean),
    ],
    resolver=delete_omics_pipeline,
)


updateOmicsPipelineStack = gql.MutationField(
    name="updateOmicsPipelineStack",
    args=[gql.Argument(name="OmicsPipelineUri", type=gql.NonNullableType(gql.String))],
    resolver=update_omics_pipeline_stack,
    type=gql.Boolean,
)
