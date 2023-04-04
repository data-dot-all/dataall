"""The module defines GraphQL queries for Omics"""
from dataall.api import gql
from dataall.modules.omics.api.resolvers import (
    get_omics_project,
    list_omics_projects,
)

getOmicsProject = gql.QueryField(
    name="getOmicsProject",
    args=[gql.Argument(name="projectUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("OmicsProject"),
    resolver=get_omics_project,
)

listSagemakerNotebooks = gql.QueryField(
    name="listOmicsProjects",
    args=[gql.Argument("filter", gql.Ref("OmicsProjectFilter"))],
    type=gql.Ref("OmicsProjectSearchResult"),
    resolver=list_omics_projects,
)

