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
        gql.Argument('secretArn', gql.String)
    ],
)

RedshiftConnectionFilter = gql.InputType(
    name='RedshiftConnectionFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument(name='environmentUri', type=gql.String),
    ],
)

