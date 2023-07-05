from dataall import gql

NewClusterInput = gql.InputType(
    name='NewClusterInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='nodeType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='numberOfNodes', type=gql.NonNullableType(gql.Integer)),
        gql.Argument(name='masterDatabaseName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='masterUsername', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='databaseName', type=gql.String),
        gql.Argument(name='vpc', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='subnetIds', type=gql.ArrayType(gql.String)),
        gql.Argument(name='securityGroupIds', type=gql.ArrayType(gql.String)),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='SamlGroupName', type=gql.String),
    ],
)

ImportClusterInput = gql.InputType(
    name='ImportClusterInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='clusterIdentifier', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='databaseName', type=gql.String),
        gql.Argument(name='SamlGroupName', type=gql.String),
    ],
)

RedshiftClusterDatasetFilter = gql.InputType(
    name='RedshiftClusterDatasetFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
