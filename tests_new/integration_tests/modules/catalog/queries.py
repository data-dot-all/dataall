# TODO: This file will be replaced by using the SDK directly

GLOSSARY_TERM_CATEGORY_COMMON_FIELDS = """
nodeUri,
parentUri,
owner,
path,
label,
status,
readme,
created,
updated,
deleted,
isMatch
"""


def create_glossary(client, name, group, read_me):
    query = {
        'operationName': 'CreateGlossary',
        'variables': {
            'input': {
                'label': name,
                'admin': group,
                'status': 'approved',
                'readme': read_me,
            }
        },
        'query': f"""
        mutation CreateGlossary($input: CreateGlossaryInput) {{
              createGlossary(input: $input) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
              }}
            }}
                """,
    }
    response = client.query(query=query)
    return response.data.createGlossary


def update_glossary(client, node_uri, name, group, read_me):
    query = {
        'operationName': 'UpdateGlossary',
        'variables': {
            'nodeUri': node_uri,
            'input': {
                'label': name,
                'admin': group,
                'status': 'SomeStatus',
                'readme': read_me,
            },
        },
        'query': f"""
            mutation UpdateGlossary($nodeUri: String!, $input: UpdateGlossaryInput) {{
              updateGlossary(nodeUri: $nodeUri, input: $input) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
              }}
            }}
            """,
    }
    response = client.query(query=query)
    return response.data.updateGlossary


def delete_glossary(client, node_uri):
    query = {
        'operationName': 'deleteGlossary',
        'variables': {'nodeUri': node_uri},
        'query': """
            mutation deleteGlossary($nodeUri: String!) {
              deleteGlossary(nodeUri: $nodeUri)
            }
            """,
    }
    response = client.query(query=query)
    return response.data.deleteGlossary


def get_glossary(client, node_uri):
    query = {
        'operationName': 'GetGlossary',
        'variables': {'nodeUri': node_uri},
        'query': f"""
            query GetGlossary($nodeUri: String!) {{
              getGlossary(nodeUri: $nodeUri) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                admin
                userRoleForGlossary
                stats {{
                  categories
                  terms
                  associations
                }}
              }}
            }}
            """,
    }
    response = client.query(query=query)
    return response.data.getGlossary


def get_glossary_tree(client, node_uri, node_type=''):
    query = {
        'operationName': 'GetGlossaryTree',
        'variables': {'nodeUri': node_uri, 'filter': {'nodeType': node_type}},
        'query': f"""
            query GetGlossaryTree(
              $nodeUri: String!
              $filter: GlossaryNodeSearchFilter
            ) {{
              getGlossary(nodeUri: $nodeUri) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                admin
                categories {{
                  count
                  page
                  pages
                  hasNext
                  hasPrevious
                  nodes {{
                    parentUri
                    {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                    stats {{
                      categories
                      terms
                    }}
                  }}
                }}
                tree(filter: $filter) {{
                  count
                  hasNext
                  hasPrevious
                  page
                  pages
                  nodes {{
                    __typename
                    ... on Glossary {{
                      {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                    }}
                    ... on Category {{
                      parentUri
                      {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                    }}
                    ... on Term {{
                      parentUri
                      {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                    }}
                  }}
                }}
              }}
            }}
            """,
    }
    response = client.query(query=query)
    return response.data.getGlossary


def list_glossary_associations(client, node_uri):
    query = {
        'operationName': 'GetGlossaryTree',
        'variables': {'nodeUri': node_uri},
        'query': f"""
            query GetGlossaryTree(
              $nodeUri: String!
              $filter: GlossaryTermTargetFilter
            ) {{
              getGlossary(nodeUri: $nodeUri) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                admin
                userRoleForGlossary
                associations(filter: $filter) {{
                  count
                  page
                  pages
                  hasNext
                  hasPrevious
                  nodes {{
                    linkUri
                    targetUri
                    approvedBySteward
                    term {{
                      label
                      nodeUri
                    }}
                    targetType
                    target {{
                      label
                    }}
                  }}
                }}
              }}
            }}
            """,
    }
    response = client.query(query=query)
    return response.data.getGlossary


def list_glossaries(client, term='', status=''):
    query = {
        'operationName': 'ListGlossaries',
        'variables': {'filter': {'term': term, 'status': status}},
        'query': f"""
            query ListGlossaries($filter: GlossaryFilter) {{
                  listGlossaries(filter: $filter) {{
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes {{
                      {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                      admin
                      stats {{
                        categories
                        terms
                        associations
                      }}
                    }}
                  }}
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.listGlossaries


def search_glossary(client, term='', node_type=''):
    query = {
        'operationName': 'SearchGlossary',
        'variables': {'filter': {'term': term, 'nodeType': node_type}},
        'query': f"""
                query SearchGlossary($filter: GlossaryNodeSearchFilter) {{
                      searchGlossary(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                          __typename
                          ... on Glossary {{
                            {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                          }}
                          ... on Category {{
                            parentUri
                            {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                          }}
                          ... on Term {{
                            parentUri
                            {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                          }}
                        }}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.searchGlossary


def create_category(client, parent_uri, name, read_me):
    query = {
        'operationName': 'CreateCategory',
        'variables': {
            'parentUri': parent_uri,
            'input': {
                'label': name,
                'status': 'approved',
                'readme': read_me,
            },
        },
        'query': f"""
                mutation CreateCategory($parentUri: String!, $input: CreateCategoryInput) {{
                  createCategory(parentUri: $parentUri, input: $input) {{
                    {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                  }}
                }}
            """,
    }
    response = client.query(query=query)
    return response.data.createCategory


def update_category(client, node_uri, name, read_me):
    query = {
        'operationName': 'UpdateCategory',
        'variables': {
            'nodeUri': node_uri,
            'input': {
                'label': name,
                'status': 'SomeStatus',
                'readme': read_me,
            },
        },
        'query': f"""
                mutation UpdateCategory($nodeUri: String!, $input: UpdateCategoryInput) {{
                  updateCategory(nodeUri: $nodeUri, input: $input) {{
                    {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                  }}
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateCategory


def delete_category(client, node_uri):
    query = {
        'operationName': 'deleteCategory',
        'variables': {'nodeUri': node_uri},
        'query': """
            mutation deleteCategory($nodeUri: String!) {
              deleteCategory(nodeUri: $nodeUri)
            }
            """,
    }
    response = client.query(query=query)
    return response.data.deleteCategory


def create_term(client, parent_uri, name, read_me):
    query = {
        'operationName': 'CreateTerm',
        'variables': {
            'parentUri': parent_uri,
            'input': {
                'label': name,
                'status': 'SomeStatus',
                'readme': read_me,
            },
        },
        'query': f"""
            mutation CreateTerm($parentUri: String!, $input: CreateTermInput) {{
              createTerm(parentUri: $parentUri, input: $input) {{
                {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
              }}
            }}
            """,
    }
    response = client.query(query=query)
    return response.data.createTerm


def update_term(client, node_uri, name, read_me):
    query = {
        'operationName': 'UpdateTerm',
        'variables': {
            'nodeUri': node_uri,
            'input': {
                'label': name,
                'status': 'SomeStatus',
                'readme': read_me,
            },
        },
        'query': f"""
                mutation UpdateTerm($nodeUri: String!, $input: UpdateTermInput) {{
                  updateTerm(nodeUri: $nodeUri, input: $input) {{
                    {GLOSSARY_TERM_CATEGORY_COMMON_FIELDS}
                  }}
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateTerm


def delete_term(client, node_uri):
    query = {
        'operationName': 'deleteTerm',
        'variables': {'nodeUri': node_uri},
        'query': """
            mutation deleteTerm($nodeUri: String!) {
              deleteTerm(nodeUri: $nodeUri)
            }
            """,
    }
    response = client.query(query=query)
    return response.data.deleteTerm


def approve_term_association(client, link_uri):
    query = {
        'operationName': 'ApproveTermAssociation',
        'variables': {'linkUri': link_uri},
        'query': """
            mutation ApproveTermAssociation($linkUri: String!) {
                  approveTermAssociation(linkUri: $linkUri)
                }
            """,
    }
    response = client.query(query=query)
    return response.data.approveTermAssociation


def dismiss_term_association(client, link_uri):
    query = {
        'operationName': 'DismissTermAssociation',
        'variables': {'linkUri': link_uri},
        'query': """
            mutation DismissTermAssociation($linkUri: String!) {
              dismissTermAssociation(linkUri: $linkUri)
            }
            """,
    }
    response = client.query(query=query)
    return response.data.dismissTermAssociation


def start_reindex_catalog(client, handle_deletes):
    query = {
        'operationName': 'startReindexCatalog',
        'variables': {'handleDeletes': handle_deletes},
        'query': """
                mutation startReindexCatalog($handleDeletes: Boolean!) {
                  startReindexCatalog(handleDeletes: $handleDeletes)
                }
                """,
    }
    response = client.query(query=query)
    return response.data.startReindexCatalog
