from dataall.base.api import gql
from dataall.base.api.constants import SortDirection
from dataall.modules.metadata_forms.api.enums import EnvironmentSortField


NewMetadataFormInput = gql.InputType(
    name='NewMetadataFormInput',
    arguments=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='visibility', type=gql.String),
        gql.Field(name='homeEntity', type=gql.String),
    ],
)

NewMetadataFormFieldInput = gql.InputType(
    name='NewMetadataFormFieldInput',
    arguments=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='type', type=gql.String),
        gql.Field(name='required', type=gql.Boolean),
        gql.Field(name='glossaryNodeUri', type=gql.String),
        gql.Field(name='possibleValues', type=gql.ArrayType(gql.String)),
    ],
)

MetadataFormSortCriteria = gql.InputType(
    name='MetadataFormSortCriteria',
    arguments=[
        gql.Argument(name='field', type=gql.NonNullableType(EnvironmentSortField.toGraphQLEnum())),
        gql.Argument(name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())),
    ],
)

MetadataFormFilter = gql.InputType(
    name='MetadataFormFilter',
    arguments=[
        gql.Argument('page', gql.Integer),
        gql.Argument('search_input', gql.String),
        gql.Argument('sort', gql.ArrayType(MetadataFormSortCriteria)),
        gql.Argument('pageSize', gql.Integer),
    ],
)
