# TODO: This file will be replaced by using the SDK directly


def list_metadata_forms(client, filter):
    query = {
        'operationName': 'listMetadataForms',
        'variables': {'filter': filter},
        'query': f"""
                  query listMetadataForms($filter: MetadataFormFilter) {{
                    listMetadataForms(filter: $filter) {{
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
    return response.data.listMetadataForms


def get_metadata_form_full_info(client, uri):
    query = {
        'operationName': 'getMetadataForm',
        'variables': {'uri': uri},
        'query': f"""
                   query getMetadataForm($uri: String!) {{
                        getMetadataForm(uri: $uri) {{
                            uri
                            name
                            description
                            SamlGroupName
                            visibility
                            homeEntity
                            homeEntityName
                            fields {{
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
