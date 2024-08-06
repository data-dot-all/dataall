from dataall.base.api import gql


CreateRedshiftConnectionInput = gql.InputType(
    name='CreateRedshiftConnectionInput',
    arguments=[
        gql.Argument('connectionName', gql.NonNullableType(gql.String)),
        gql.Argument('connectionType', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('redshiftType', gql.NonNullableType(gql.String)),
        gql.Argument('clusterId', gql.String),
        gql.Argument('nameSpaceId', gql.String),
        gql.Argument('workgroup', gql.String),
        gql.Argument('database', gql.NonNullableType(gql.String)),
        gql.Argument('redshiftUser', gql.String),
        gql.Argument('secretArn', gql.String),
    ],
)


ConnectionFilter = gql.InputType(
    name='ConnectionFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('environmentUri', gql.String),
        gql.Argument('groupUri', gql.String),
        gql.Argument('connectionType', gql.String),
    ],
)
