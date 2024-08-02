from dataall.base.api import gql


ImportRedshiftDatasetInput = gql.InputType(
    name='ImportRedshiftDatasetInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('owner', gql.NonNullableType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('confidentiality', gql.String),
        gql.Argument('stewards', gql.String),
        gql.Argument('autoApprovalEnabled', gql.Boolean),
        gql.Argument('connectionUri', gql.NonNullableType(gql.String)),
        gql.Argument('schema', gql.NonNullableType(gql.String)),
        gql.Argument('tables', gql.ArrayType(gql.String)),
    ],
)


ModifyRedshiftDatasetInput = gql.InputType(
    name='ModifyRedshiftDatasetInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument('terms', gql.ArrayType(gql.String)),
        gql.Argument('confidentiality', gql.String),
        gql.Argument('stewards', gql.String),
        gql.Argument('autoApprovalEnabled', gql.Boolean),
    ],
)

RedshiftDatasetTableFilter = gql.InputType(
    name='RedshiftDatasetTableFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
