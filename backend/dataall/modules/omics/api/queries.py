"""The module defines GraphQL queries for Omics Pipelines"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql
from .resolvers import *

listOmicsPipelines = gql.QueryField(
    name="listOmicsPipelines",
    args=[gql.Argument(name="filter", type=gql.Ref("OmicsPipelineFilter"))],
    resolver=list_pipelines,
    type=gql.Ref("OmicsPipelineSearchResults"),
)

getOmicsPipeline = gql.QueryField(
    name="getOmicsPipeline",
    args=[gql.Argument(name="OmicsPipelineUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("OmicsPipeline"),
    resolver=get_omics_pipeline,
)

