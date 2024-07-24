from dataall.base.api import gql
from dataall.modules.metadata_forms.api.input_types import MetadataFormFilter
from dataall.modules.metadata_forms.api.resolvers import list_metadata_forms
from dataall.modules.metadata_forms.api.types import MetadataFormSearchResult

listMetadataForms = gql.QueryField(
    name='listMetadataForms',
    args=[gql.Argument('filter', MetadataFormFilter)],
    type=MetadataFormSearchResult,
    resolver=list_metadata_forms,
    test_scope='MetadataForm',
)
