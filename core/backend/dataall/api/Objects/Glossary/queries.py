from ... import gql
from .resolvers import *

getGlossary = gql.QueryField(
    name='getGlossary',
    args=[gql.Argument(name='nodeUri', type=gql.NonNullableType(gql.String))],
    resolver=get_node,
    type=gql.Ref('Glossary'),
)


getCategory = gql.QueryField(
    name='getCategory',
    resolver=get_node,
    args=[gql.Argument(name='nodeUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Category'),
)


getTerm = gql.QueryField(
    name='getTerm',
    resolver=get_node,
    args=[gql.Argument(name='nodeUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Term'),
)

listGlossaries = gql.QueryField(
    name='listGlossaries',
    type=gql.Ref('GlossarySearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('GlossaryFilter'))],
    resolver=list_glossaries,
)


SearchTerms = gql.QueryField(
    name='searchTerms',
    doc='Search glossary terms',
    type=gql.Ref('TermSearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('TermFilter'))],
    resolver=search_terms,
)


searchGlossaryHierarchy = gql.QueryField(
    name='searchGlossaryHierarchy',
    doc='Search glossary terms in the hierarchy',
    type=gql.Ref('GlossaryChildrenSearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('TermFilter'))],
    resolver=hierarchical_search,
)


SearchGlossary = gql.QueryField(
    name='searchGlossary',
    doc='Search glossary ',
    type=gql.Ref('GlossaryChildrenSearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('GlossaryNodeSearchFilter'))],
    resolver=search_terms,
)


getGlossaryTermLink = gql.QueryField(
    name='getGlossaryTermLink',
    doc='Returns a TermLink from its linkUri',
    type=gql.Ref('GlossaryTermLink'),
    resolver=get_link,
    args=[gql.Argument(name='linkUri', type=gql.NonNullableType(gql.String))],
)

listAssetLinkedTerms = gql.QueryField(
    name='listAssetLinkedTerms',
    doc='return all terms associated with a data asset',
    args=[
        gql.Argument(name='uri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GlossaryTermTargetFilter')),
    ],
    resolver=list_asset_linked_terms,
    type=gql.Ref('TermLinkSearchResults'),
)
