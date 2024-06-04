from dataall.base.api import gql


CreateRedshiftConnectionInput = gql.InputType(
    name='CreateRedshiftConnectionInput',
    arguments=[
        gql.Argument('connectionName', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('redshiftType', gql.NonNullableType(gql.String)),
        gql.Argument('clusterId', gql.String),
        gql.Argument('nameSpaceId', gql.String),
        gql.Argument('workgroupId', gql.String),
        gql.Argument('redshiftUser', gql.String),
        gql.Argument('secretArn', gql.String),
    ],
)
