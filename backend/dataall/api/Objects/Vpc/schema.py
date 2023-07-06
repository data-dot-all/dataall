from dataall.base.api import gql

Vpc = gql.ObjectType(
    name='Vpc',
    fields=[
        gql.Field(name='VpcId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='vpcUri', type=gql.NonNullableType(gql.ID)),
        gql.Field(name='environment', type=gql.Ref('Environment')),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='AwsAccountId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='region', type=gql.NonNullableType(gql.String)),
        gql.Field(name='privateSubnetIds', type=gql.ArrayType(gql.String)),
        gql.Field(name='publicSubnetIds', type=gql.ArrayType(gql.String)),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='default', type=gql.Boolean),
    ],
)
VpcSearchResult = gql.ObjectType(
    name='VpcSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('Vpc'))),
    ],
)
