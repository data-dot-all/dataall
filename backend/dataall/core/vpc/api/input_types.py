from dataall.base.api import gql

VpcFilter = gql.InputType(
    name='VpcFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

NewVpcInput = gql.InputType(
    name='NewVpcInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='vpcId', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='publicSubnetIds', type=gql.ArrayType(gql.String)),
        gql.Argument(name='privateSubnetIds', type=gql.ArrayType(gql.String)),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='SamlGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
    ],
)
