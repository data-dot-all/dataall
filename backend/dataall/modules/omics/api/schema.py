#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql
from .resolvers import *
from dataall.modules.omics.api.enums import OmicsPipelineRole
from dataall.api.Objects.Organization.resolvers import resolve_organization_by_env
from dataall.api.Objects.Environment.resolvers import resolve_environment

OmicsPipeline = gql.ObjectType(
    name="OmicsPipeline",
    fields=[
        gql.Field("OmicsPipelineUri", type=gql.ID),
        gql.Field("environmentUri", type=gql.String),
        gql.Field("organizationUri", type=gql.String),
        gql.Field("name", type=gql.String),
        gql.Field("label", type=gql.String),
        gql.Field("description", type=gql.String),
        gql.Field("tags", type=gql.ArrayType(gql.String)),
        gql.Field("created", type=gql.String),
        gql.Field("updated", type=gql.String),
        gql.Field("owner", type=gql.String),
        gql.Field("CodeRepository", type=gql.String),
        gql.Field("AwsAccountId", type=gql.String),
        gql.Field("region", type=gql.String),
        gql.Field("CiPipeline", type=gql.String),
        gql.Field("StepFunction", type=gql.String),
        gql.Field("OmicsWorkflow", type=gql.String),
        gql.Field("CiPipelineStatus", type=gql.String, resolver=resolve_cipipeline_status),
        gql.Field("StepFunctionStatus", type=gql.String, resolver=resolve_step_function_status),
        gql.Field("OmicsWorkflowStatus", type=gql.String, resolver=resolve_workflow_status),
        gql.Field("SamlGroupName", type=gql.String),
        gql.Field("AwsResources", type=gql.String),
        gql.Field("environment", type=gql.Ref("Environment"), resolver=resolve_environment),
        gql.Field("organization", type=gql.Ref("Organization"), resolver=resolve_organization_by_env),
        gql.Field("S3InputBucket", type=gql.String),
        gql.Field("S3InputPrefix", type=gql.String),
        gql.Field("S3OutputBucket", type=gql.String),
        gql.Field("S3OutputPrefix", type=gql.String),
        gql.Field("stack", gql.Ref("Stack"), resolver=resolve_omics_pipeline_stack),
        gql.Field(
            "userRoleForPipeline",
            type=OmicsPipelineRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
    ],
)


OmicsPipelineSearchResults = gql.ObjectType(
    name="OmicsPipelineSearchResults",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(OmicsPipeline)),
    ],
)