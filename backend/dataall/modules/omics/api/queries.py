"""The module defines GraphQL queries for Omics uns"""

from dataall.base.api import gql
from .resolvers import *

listOmicsRuns = gql.QueryField(
    name="listOmicsRuns",
    args=[gql.Argument(name="filter", type=gql.Ref("OmicsFilter"))],
    resolver=list_omics_runs,
    type=gql.Ref("OmicsRunSearchResults"),
)

getOmicsWorkflow = gql.QueryField(
    name="getOmicsWorkflow",
    args=[gql.Argument(name="workflowId", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("OmicsWorkflow"),
    resolver=get_omics_workflow,
)

listOmicsWorkflows = gql.QueryField(
    name="listOmicsWorkflows",
    args=[gql.Argument(name="filter", type=gql.Ref("OmicsFilter"))],
    type=gql.Ref("OmicsWorkflows"),
    resolver=list_omics_workflows,
)

getWorkflowRun = gql.QueryField(
    name="getWorkflowRun",
    args=[gql.Argument(name="runId", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("OmicsRunStatus"),
    resolver=get_workflow_run,
)

runOmicsWorkflow = gql.QueryField(
    name="runOmicsWorkflow",
    args=[gql.Argument(name="workflowId", type=gql.NonNullableType(gql.String)), gql.Argument(name="workflowType", type=gql.NonNullableType(gql.String)), gql.Argument(name="roleArn", type=gql.NonNullableType(gql.String)), gql.Argument(name="parameters", type=gql.NonNullableType(gql.String)) ],
    type=gql.Ref("RunOmicsWorkflowStatus"),
    resolver=run_omics_workflow,
)
