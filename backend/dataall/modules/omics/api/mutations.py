"""The module defines GraphQL mutations for Omics Projects"""
from dataall.api import gql
from dataall.modules.omics.api.resolvers import (
    create_omics_project,
    delete_omics_project
)

createOmicsProject = gql.MutationField(
    name="createOmicsProject",
    args=[gql.Argument(name="input", type=gql.Ref("NewOmicsProjectInput"))],
    type=gql.Ref("OmicsProject"),
    resolver=create_omics_project,
)


deleteOmicsProject = gql.MutationField(
    name="deleteOmicsProject",
    args=[
        gql.Argument(name="projectUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="deleteFromAWS", type=gql.Boolean),
    ],
    type=gql.String,
    resolver=delete_omics_project,
)
