"""The module defines GraphQL input types for the SageMaker ML Studio"""
from dataall.base.api import gql

NewSagemakerStudioUserInput = gql.InputType(
    name='NewSagemakerStudioUserInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.String),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
    ],
)

ModifySagemakerStudioUserInput = gql.InputType(
    name='ModifySagemakerStudioUserInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('description', gql.String),
    ],
)

SagemakerStudioUserFilter = gql.InputType(
    name='SagemakerStudioUserFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('sort', gql.String),
        gql.Argument('limit', gql.Integer),
        gql.Argument('offset', gql.Integer),
    ],
)

SagemakerStudioDomainFilter = gql.InputType(
    name='SagemakerStudioDomainFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

NewStudioDomainInput = gql.InputType(
    name='NewStudioDomainInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('subnetIds', gql.ArrayType(gql.String)),
        gql.Argument('vpcId', gql.String),
    ],
)
