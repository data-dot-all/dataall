from ... import gql
from ....api.constants import PrincipalType


Principal = gql.ObjectType(
    name='Principal',
    fields=[
        gql.Field(name='principalId', type=gql.ID),
        gql.Field(name='principalType', type=PrincipalType.toGraphQLEnum()),
        gql.Field(name='principalName', type=gql.String),
        gql.Field(name='principalIAMRoleName', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='environmentName', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='organizationName', type=gql.String),
        gql.Field(name='organizationUri', type=gql.String),
    ],
)


PrincipalSearchResult = gql.ObjectType(
    name='PrincipalSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(Principal)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
