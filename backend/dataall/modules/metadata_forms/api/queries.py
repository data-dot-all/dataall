from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import list_metadata_forms, get_metadata_form

listMetadataForms = gql.QueryField(
    name='listMetadataForms',
    args=[gql.Argument('filter', gql.Ref('MetadataFormFilter'))],
    type=gql.Ref('MetadataFormSearchResult'),
    resolver=list_metadata_forms,
    test_scope='MetadataForm',
)

getMetadataForm = gql.QueryField(
    name='getMetadataForm',
    args=[gql.Argument('uri', gql.NonNullableType(gql.String))],
    type=gql.Ref('MetadataForm'),
    resolver=get_metadata_form,
    test_scope='MetadataForm',
)
