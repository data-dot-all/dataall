"""Defines the object types of the Omics projects"""
from dataall.api import gql
from dataall.modules.omics.api.resolvers import (
    resolve_omics_stack,
    resolve_user_role,
)

from dataall.api.Objects.Environment.resolvers import resolve_environment
from dataall.api.Objects.Organization.resolvers import resolve_organization_by_env

from dataall.modules.omics.api.enums import OmicsProjectRole

#TODO: Define GraphQL object types
OmicsProject = gql.ObjectType(
    name="OmicsProject",
    fields=[
        gql.Field(name="projectUri", type=gql.ID),
        gql.Field(name="environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Field(name="label", type=gql.String),
        gql.Field(name="description", type=gql.String),
        gql.Field(name="tags", type=gql.ArrayType(gql.String)),
        gql.Field(name="name", type=gql.String),
        gql.Field(name="owner", type=gql.String),
        gql.Field(name="created", type=gql.String),
        gql.Field(name="updated", type=gql.String),
        gql.Field(name="SamlAdminGroupName", type=gql.String),
        gql.Field(
            name="userRoleForNotebook",
            type=OmicsProjectRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name="environment",
            type=gql.Ref("Environment"),
            resolver=resolve_environment,
        ),
        gql.Field(
            name="organization",
            type=gql.Ref("Organization"),
            resolver=resolve_organization_by_env,
        ),
        gql.Field(name="stack", type=gql.Ref("Stack"), resolver=resolve_omics_stack),
    ],
)

OmicsProjectSearchResult = gql.ObjectType(
    name="OmicsProjectSearchResult",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(OmicsProject)),
    ],
)
