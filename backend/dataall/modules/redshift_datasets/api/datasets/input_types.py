from dataall.base.api import gql


ImportRedshiftDatasetInput = gql.InputType(
    name='ImportRedshiftDatasetInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('adminRoleName', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('owner', gql.NonNullableType(gql.String)),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='businessOwnerEmail', type=gql.String),
        gql.Argument(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Argument('confidentiality', gql.String),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument(name='autoApprovalEnabled', type=gql.Boolean),
        gql.Argument('connectionUri', gql.NonNullableType(gql.String)),
        gql.Argument('schema', gql.NonNullableType(gql.String)),
        gql.Argument(name='tables', type=gql.ArrayType(gql.String)),
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
        gql.Argument('businessOwnerDelegationEmails', gql.ArrayType(gql.String)),
        gql.Argument('businessOwnerEmail', gql.String),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('confidentiality', gql.String),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)

RedshiftDatasetTableFilter = gql.InputType(  # TODO: this filter should be generic in Core, very duplicated
    name='RedshiftDatasetTableFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
