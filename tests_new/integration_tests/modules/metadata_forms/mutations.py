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


def create_metadata_form_fields(client, formUri, input):
    query = {
        'operationName': 'createMetadataFormFields',
        'variables': {'formUri': formUri, 'input': input},
        'query': f"""
                  mutation createMetadataFormFields($formUri: String!, $input: [NewMetadataFormFieldInput]) {{
                    createMetadataFormFields(formUri: $formUri, input: $input) {{
                        uri
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.createMetadataFormFields


def delete_metadata_form_field(client, formUri, fieldUri):
    query = {
        'operationName': 'deleteMetadataFormField',
        'variables': {'formUri': formUri, 'fieldUri': fieldUri},
        'query': f"""
                  mutation deleteMetadataFormField($formUri: String!, $fieldUri: String!)  {{
                    deleteMetadataFormField(formUri: $formUri, fieldUri: $fieldUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteMetadataFormField


def update_metadata_form_fields(client, formUri, input):
    query = {
        'operationName': 'batchMetadataFormFieldUpdates',
        'variables': {'formUri': formUri, 'input': input},
        'query': f"""
                   mutation batchMetadataFormFieldUpdates(
                        $formUri: String!
                        $input: [MetadataFormFieldUpdateInput]
                        ) {{
                        batchMetadataFormFieldUpdates(formUri: $formUri, input: $input) {{
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
                """,
    }
    response = client.query(query=query)
    return response.data.batchMetadataFormFieldUpdates
