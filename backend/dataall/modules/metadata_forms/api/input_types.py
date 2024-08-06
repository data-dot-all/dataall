from dataall.base.api import gql

NewMetadataFormInput = gql.InputType(
    name='NewMetadataFormInput',
    arguments=[
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='visibility', type=gql.NonNullableType(gql.String)),
        gql.Field(name='homeEntity', type=gql.String),
    ],
)


MetadataFormFilter = gql.InputType(
    name='MetadataFormFilter',
    arguments=[
        gql.Argument('page', gql.Integer),
        gql.Argument('search_input', gql.String),
        gql.Argument('pageSize', gql.Integer),
    ],
)
