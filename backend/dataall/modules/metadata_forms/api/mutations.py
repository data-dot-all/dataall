from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import (
    create_metadata_form,
    delete_metadata_form,
    create_metadata_form_fields,
    delete_metadata_form_field,
    batch_metadata_form_field_update,
)

createMetadataForm = gql.MutationField(
    name='createMetadataForm',
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('NewMetadataFormInput')))],
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

createMetadataFormFields = gql.MutationField(
    name='createMetadataFormFields',
    args=[
        gql.Argument(name='formUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.ArrayType(gql.Ref('NewMetadataFormFieldInput'))),
    ],
    type=gql.ArrayType(gql.Ref('MetadataFormField')),
    resolver=create_metadata_form_fields,
    test_scope='MetadataForm',
)

deleteMetadataFormField = gql.MutationField(
    name='deleteMetadataFormField',
    args=[
        gql.Argument(name='formUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='fieldUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=delete_metadata_form_field,
    test_scope='MetadataForm',
)

batchMetadataFormFieldUpdates = gql.MutationField(
    name='batchMetadataFormFieldUpdates',
    args=[
        gql.Argument(name='formUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.ArrayType(gql.Ref('MetadataFormFieldUpdateInput'))),
    ],
    type=gql.ArrayType(gql.Ref('MetadataFormField')),
    resolver=batch_metadata_form_field_update,
    test_scope='MetadataForm',
)
