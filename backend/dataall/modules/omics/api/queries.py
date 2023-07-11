"""The module defines GraphQL queries for Omics uns"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql
from .resolvers import *

listOmicsRuns = gql.QueryField(
    name="listOmicsRuns",
    args=[gql.Argument(name="filter", type=gql.Ref("OmicsRunFilter"))],
    resolver=list_omics_runs,
    type=gql.Ref("OmicRunSearchResults"),
)

getOmicWorkflow = gql.QueryField(
    name="getOmicsWorkflow",
    args=[gql.Argument(name="workflowUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("OmicsRun"),
    resolver=get_omics_workflow,
)

