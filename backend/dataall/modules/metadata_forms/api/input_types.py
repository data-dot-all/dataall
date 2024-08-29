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

NewMetadataFormFieldInput = gql.InputType(
    name='NewMetadataFormFieldInput',
    arguments=[
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='type', type=gql.NonNullableType(gql.String)),
        gql.Field(name='displayNumber', type=gql.NonNullableType(gql.Integer)),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='required', type=gql.Boolean),
        gql.Field(name='glossaryNodeUri', type=gql.String),
        gql.Field(name='possibleValues', type=gql.ArrayType(gql.String)),
    ],
)

MetadataFormFieldUpdateInput = gql.InputType(
    name='MetadataFormFieldUpdateInput',
    arguments=[
        gql.Field(name='uri', type=gql.String),
        gql.Field(name='metadataFormUri', type=gql.String),
        gql.Field(name='displayNumber', type=gql.NonNullableType(gql.Integer)),
        gql.Field(name='deleted', type=gql.Boolean),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='type', type=gql.String),
        gql.Field(name='required', type=gql.Boolean),
        gql.Field(name='glossaryNodeUri', type=gql.String),
        gql.Field(name='possibleValues', type=gql.ArrayType(gql.String)),
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
