from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import create_metadata_form, delete_metadata_form
from dataall.modules.metadata_forms.api.input_types import NewMetadataFormInput

createMetadataForm = gql.MutationField(
    name='createMetadataForm',
    args=[gql.Argument(name='input', type=gql.NonNullableType(NewMetadataFormInput))],
    type=gql.Ref('MetadataForm'),
    resolver=create_metadata_form,
    test_scope='MetadataForm',
)

deleteMetadataForm = gql.MutationField(
    name='deleteMetadataForm',
    args=[
        gql.Argument(name='formUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=delete_metadata_form,
    test_scope='MetadataForm',
)
