from dataall.base.api import gql
from .resolvers import *
from dataall.modules.omics.api.enums import OmicsRunRole
from dataall.core.organizations.api.resolvers import resolve_organization_by_env
from dataall.core.environment.api.resolvers import resolve_environment

OmicsRun = gql.ObjectType(
    name="OmicsRun",
    fields=[
        gql.Field("OmicsRunUri", type=gql.ID),
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
        gql.Field("SamlGroupName", type=gql.String),
        gql.Field("AwsResources", type=gql.String),
        gql.Field("environment", type=gql.Ref("Environment"), resolver=resolve_environment),
        gql.Field("organization", type=gql.Ref("Organization"), resolver=resolve_organization_by_env),
        gql.Field("S3InputBucket", type=gql.String),
        gql.Field("S3InputPrefix", type=gql.String),
        gql.Field("S3OutputBucket", type=gql.String),
        gql.Field("S3OutputPrefix", type=gql.String),
        gql.Field(
            "userRoleForPipeline",
            type=OmicsRunRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
    ],
)


OmicsRunSearchResults = gql.ObjectType(
    name="OmicsRunSearchResults",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(OmicsRun)),
    ],
)

OmicsWorkflow = gql.ObjectType(
    name="OmicsWorkflow",
    fields=[
        gql.Field(name="arn", type=gql.String),
        # gql.Field(name="creationTime", type=gql.String),
        # gql.Field(name="digest", type=gql.String),
        gql.Field(name="id", type=gql.String),
        gql.Field(name="name", type=gql.String),
        gql.Field(name="status", type=gql.String),
        gql.Field(name="type", type=gql.String),
        gql.Field(name="description", type=gql.String),
    ],
)

OmicsWorkflows = gql.ObjectType(
    name="OmicsWorkflows",
    fields=[
        # gql.Field(name="count", type=gql.Integer),
        # gql.Field(name="page", type=gql.Integer),
        # gql.Field(name="pages", type=gql.Integer),
        # gql.Field(name="hasNext", type=gql.Boolean),
        # gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(OmicsWorkflow)),
    ],
)