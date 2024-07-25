from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import list_metadata_forms

listMetadataForms = gql.QueryField(
    name='listMetadataForms',
    args=[gql.Argument('filter', gql.Ref('MetadataFormFilter'))],
    type=gql.Ref('MetadataFormSearchResult'),
    resolver=list_metadata_forms,
    test_scope='MetadataForm',
)

