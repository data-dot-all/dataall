"""The module defines GraphQL input types for the SageMaker notebooks"""

from dataall.base.api import gql

NewSagemakerNotebookInput = gql.InputType(
    name='NewSagemakerNotebookInput ',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.String),
        gql.Argument('VpcId', gql.String),
        gql.Argument('SubnetId', gql.String),
        gql.Argument('VolumeSizeInGB', gql.Integer),
        gql.Argument('InstanceType', gql.String),
    ],
)

ModifySagemakerNotebookInput = gql.InputType(
    name='ModifySagemakerNotebookInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('description', gql.String),
    ],
)

SagemakerNotebookFilter = gql.InputType(
    name='SagemakerNotebookFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('sort', gql.String),
        gql.Argument('limit', gql.Integer),
        gql.Argument('offset', gql.Integer),
    ],
)
