def update_stack(client, target_uri, target_type):
    query = {
        'operationName': 'updateStack',
        'variables': {'targetUri': target_uri, 'targetType': target_type},
        'query': """
                    mutation updateStack($targetUri: String!, $targetType: String!) {
                      updateStack(targetUri: $targetUri, targetType: $targetType) {
                        stackUri
                        targetUri
                        name
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.updateStack


def get_stack(client, env_uri, stack_uri, target_uri, target_type):
    query = {
        'operationName': 'getStack',
        'variables': {
            'environmentUri': env_uri,
            'stackUri': stack_uri,
            'targetUri': target_uri,
            'targetType': target_type,
        },
        'query': """
                    query getStack(
                      $environmentUri: String!
                      $stackUri: String!
                      $targetUri: String!
                      $targetType: String!
                    ) {
                      getStack(
                        environmentUri: $environmentUri
                        stackUri: $stackUri
                        targetUri: $targetUri
                        targetType: $targetType
                      ) {
                        status
                        stackUri
                        targetUri
                        accountid
                        region
                        stackid
                        link
                        outputs
                        resources
                        error
                        events
                        name
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.getStack
