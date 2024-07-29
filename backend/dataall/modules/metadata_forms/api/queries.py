from dataall.base.api import gql
from dataall.base.utils.enum_utils import generate_enum_query
from dataall.modules.metadata_forms.api.resolvers import list_metadata_forms
from dataall.modules.metadata_forms.db.enums import MetadataFormVisibility

listMetadataForms = gql.QueryField(
    name='listMetadataForms',
    args=[gql.Argument('filter', gql.Ref('MetadataFormFilter'))],
    type=gql.Ref('MetadataFormSearchResult'),
    resolver=list_metadata_forms,
    test_scope='MetadataForm',
)

queryMetadataFormVisibility = generate_enum_query(MetadataFormVisibility, 'MetadataForm')
