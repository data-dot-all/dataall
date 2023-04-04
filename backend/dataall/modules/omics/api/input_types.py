"""The module defines GraphQL input types for Omics Projects"""
from dataall.api import gql

NewOmicsProjectInput = gql.InputType(
    name="NewOmicsProjectInput",
    arguments=[
        gql.Argument("label", gql.NonNullableType(gql.String)),
        gql.Argument("description", gql.String),
        gql.Argument("environmentUri", gql.NonNullableType(gql.String)),
        gql.Argument("SamlAdminGroupName", gql.NonNullableType(gql.String)),
        gql.Argument("tags", gql.ArrayType(gql.String)),
        gql.Argument("topics", gql.String),
        gql.Argument("VpcId", gql.String),
        gql.Argument("SubnetId", gql.String),
    ],
)

ModifyOmicsProjectInput = gql.InputType(
    name="ModifyOmicsProjectInput",
    arguments=[
        gql.Argument("label", gql.String),
        gql.Argument("tags", gql.ArrayType(gql.String)),
        gql.Argument("description", gql.String),
    ],
)

OmicsProjectFilter = gql.InputType(
    name="OmicsProjectFilter",
    arguments=[
        gql.Argument("term", gql.String),
        gql.Argument("page", gql.Integer),
        gql.Argument("pageSize", gql.Integer)
    ],
)
