# TODO: This file will be replaced by using the SDK directly


def list_user_metadata_forms(client, filter):
    query = {
        'operationName': 'listUserMetadataForms',
        'variables': {'filter': filter},
        'query': f"""
                  query listUserMetadataForms($filter: MetadataFormFilter) {{
                    listUserMetadataForms(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                            uri
                            name
                            description
                            SamlGroupName
                            visibility
                            homeEntity
                            homeEntityName
                        }}
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.listUserMetadataForms


def get_metadata_form_full_info(client, uri, version=None):
    query = {
        'operationName': 'getMetadataForm',
        'variables': {'uri': uri, 'version': version},
        'query': f"""
                   query getMetadataForm($uri: String!, $version: Int) {{
                        getMetadataForm(uri: $uri) {{
                            uri
                            name
                            description
                            SamlGroupName
                            visibility
                            homeEntity
                            homeEntityName
                            fields (version: $version) {{
                                uri
                                metadataFormUri
                                name
                                displayNumber
                                description
                                required
                                type
                                glossaryNodeUri
                                possibleValues
                            }}
                        }}
                   }}
                """,
    }
    response = client.query(query=query)
    return response.data.getMetadataForm
