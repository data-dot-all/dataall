# TODO: This file will be replaced by using the SDK directly


def create_metadata_form(client, input):
    query = {
        'operationName': 'createMetadataForm',
        'variables': {'input': input},
        'query': f"""
                  mutation createMetadataForm($input: NewMetadataFormInput!) {{
                    createMetadataForm(input: $input) {{
                        uri
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.createMetadataForm


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


def delete_metadata_form(client, uri):
    query = {
        'operationName': 'deleteMetadataForm',
        'variables': {'formUri': uri},
        'query': f"""
                  mutation deleteMetadataForm($formUri: String!) {{
                    deleteMetadataForm(formUri: $formUri)
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteMetadataForm
