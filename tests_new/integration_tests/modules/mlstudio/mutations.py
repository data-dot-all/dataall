def create_smstudio_user(
    client, environmentUri, groupName, label, description='integtestmlstudio', tags=[], topics=None
):
    query = {
        'operationName': 'createSagemakerStudioUser',
        'variables': {
            'input': {
                'environmentUri': environmentUri,
                'SamlAdminGroupName': groupName,
                'label': label,
                'description': description,
                'tags': tags,
                'topics': topics,
            }
        },
        'query': f"""
                    mutation createSagemakerStudioUser($input: NewSagemakerStudioUserInput!) {{
                        createSagemakerStudioUser(input: $input) {{
                            sagemakerStudioUserUri
                            name
                            label
                            created
                            description
                            tags
                            stack {{
                                stack
                                status
                                stackUri
                            }}
                        }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createSagemakerStudioUser


def delete_smstudio_user(client, uri, delete_from_aws=True):
    query = {
        'operationName': 'deleteSagemakerStudioUser',
        'variables': {
            'sagemakerStudioUserUri': uri,
            'deleteFromAWS': delete_from_aws,
        },
        'query': f"""
                    mutation deleteSagemakerStudioUser(
                      $sagemakerStudioUserUri: String!
                      $deleteFromAWS: Boolean
                    ) {{
                        deleteSagemakerStudioUser(
                            sagemakerStudioUserUri: $sagemakerStudioUserUri
                            deleteFromAWS: $deleteFromAWS
                        )
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteSagemakerStudioUser
