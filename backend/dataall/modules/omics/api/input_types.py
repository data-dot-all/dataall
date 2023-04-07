"""The module defines GraphQL input types for Omics Pipelines"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api import gql

NewOmicsPipelineInput = gql.InputType(
    name="NewOmicsPipelineInput",
    arguments=[
        gql.Field("environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Field("label", type=gql.NonNullableType(gql.String)),
        gql.Field("description", type=gql.String),
        gql.Field("tags", type=gql.ArrayType(gql.String)),
        gql.Field("created", type=gql.String),
        gql.Field("updated", type=gql.String),
        gql.Field("owner", type=gql.String),
        gql.Field("SamlGroupName", type=gql.NonNullableType(gql.String)),
        gql.Field("S3InputBucket", type=gql.NonNullableType(gql.String)),
        gql.Field("S3InputPrefix", type=gql.NonNullableType(gql.String)),
        gql.Field("S3OutputBucket", type=gql.NonNullableType(gql.String)),
        gql.Field("S3OutputPrefix", type=gql.NonNullableType(gql.String)),
    ],
)

UpdateOmicsPipelineInput = gql.InputType(
    name="UpdateOmicsPipelineInput",
    arguments=[
        gql.Argument(name="label", type=gql.String),
        gql.Argument(name="description", type=gql.String),
        gql.Argument(name="tags", type=gql.ArrayType(gql.String)),
        gql.Argument(name="S3InputBucket", type=gql.String),
        gql.Argument(name="S3InputPrefix", type=gql.String),
        gql.Argument(name="S3OutputBucket", type=gql.String),
        gql.Argument(name="S3OutputPrefix", type=gql.String),
    ],
)

OmicsPipelineFilter = gql.InputType(
    name="OmicsPipelineFilter",
    arguments=[
        gql.Argument(name="term", type=gql.String),
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)
