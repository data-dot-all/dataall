from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import (
    list_metadata_forms,
    get_metadata_form,
    get_attached_metadata_form, list_attached_forms,
)

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

listAttachedMetadataForms = gql.QueryField(
    name='listAttachedMetadataForms',
    args=[gql.Argument('filter', gql.Ref('AttachedMetadataFormFilter'))],
    type=gql.Ref('AttachedMetadataFormSearchResult'),
    resolver=list_attached_forms,
    test_scope='MetadataForm',
)


getAttachedMetadataForm = gql.QueryField(
    name='getAttachedMetadataForm',
    args=[gql.Argument('uri', gql.NonNullableType(gql.String))],
    type=gql.Ref('AttachedMetadataForm'),
    resolver=get_attached_metadata_form,
    test_scope='MetadataForm',
)