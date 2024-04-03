"""The module defines GraphQL queries for Omics runs"""

from dataall.base.api import gql
from .resolvers import *

listOmicsRuns = gql.QueryField(
    name='listOmicsRuns',
    args=[gql.Argument(name='filter', type=gql.Ref('OmicsFilter'))],
    resolver=list_omics_runs,
    type=gql.Ref('OmicsRunSearchResults'),
)

getOmicsWorkflow = gql.QueryField(
    name='getOmicsWorkflow',
    args=[gql.Argument(name='workflowUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('OmicsWorkflow'),
    resolver=get_omics_workflow,
)

listOmicsWorkflows = gql.QueryField(
    name='listOmicsWorkflows',
    args=[gql.Argument(name='filter', type=gql.Ref('OmicsFilter'))],
    type=gql.Ref('OmicsWorkflows'),
    resolver=list_omics_workflows,
)
