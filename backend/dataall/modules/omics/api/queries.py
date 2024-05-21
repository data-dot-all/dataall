"""The module defines GraphQL queries for Omics runs"""

from dataall.base.api import gql
from .resolvers import list_omics_runs, get_omics_workflow, list_omics_workflows
from .types import OmicsRunSearchResults, OmicsWorkflow, OmicsWorkflows
from .input_types import OmicsFilter

listOmicsRuns = gql.QueryField(
    name='listOmicsRuns',
    args=[gql.Argument(name='filter', type=OmicsFilter)],
    resolver=list_omics_runs,
    type=OmicsRunSearchResults,
)

getOmicsWorkflow = gql.QueryField(
    name='getOmicsWorkflow',
    args=[gql.Argument(name='workflowUri', type=gql.NonNullableType(gql.String))],
    type=OmicsWorkflow,
    resolver=get_omics_workflow,
)

listOmicsWorkflows = gql.QueryField(
    name='listOmicsWorkflows',
    args=[gql.Argument(name='filter', type=OmicsFilter)],
    type=OmicsWorkflows,
    resolver=list_omics_workflows,
)
