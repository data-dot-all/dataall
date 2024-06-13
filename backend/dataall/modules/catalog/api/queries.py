from dataall.base.api import gql
from dataall.modules.catalog.api.resolvers import (
    get_node,
    list_glossaries,
    search_glossary,
)

getGlossary = gql.QueryField(
    name='getGlossary',
    args=[gql.Argument(name='nodeUri', type=gql.NonNullableType(gql.String))],
    resolver=get_node,
    type=gql.Ref('Glossary'),
)

listGlossaries = gql.QueryField(
    name='listGlossaries',
    type=gql.Ref('GlossarySearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('GlossaryFilter'))],
    resolver=list_glossaries,
)

SearchGlossary = gql.QueryField(
    name='searchGlossary',
    description='Search glossary ',
    type=gql.Ref('GlossaryChildrenSearchResult'),
    args=[gql.Argument(name='filter', type=gql.Ref('GlossaryNodeSearchFilter'))],
    resolver=search_glossary,
)
