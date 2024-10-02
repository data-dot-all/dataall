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
                        updated
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


def get_stack_logs(client, target_uri, target_type):
    query = {
        'operationName': 'getStackLogs',
        'variables': {
            'targetUri': target_uri,
            'targetType': target_type,
        },
        'query': """
                query getStackLogs($targetUri: String!, $targetType: String!) {
                  getStackLogs(targetUri: $targetUri, targetType: $targetType) {
                    message
                    timestamp
                  }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.getStackLogs


def list_key_value_tags(client, target_uri, target_type):
    query = {
        'operationName': 'listKeyValueTags',
        'variables': {
            'targetUri': target_uri,
            'targetType': target_type,
        },
        'query': """
                query listKeyValueTags($targetUri: String!, $targetType: String!) {
                  listKeyValueTags(targetUri: $targetUri, targetType: $targetType) {
                    tagUri
                    targetUri
                    targetType
                    key
                    value
                    cascade
                  }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.listKeyValueTags


def update_key_value_tags(client, input):
    query = {
        'operationName': 'updateKeyValueTags',
        'variables': {'input': input},
        'query': """
                mutation updateKeyValueTags($input: UpdateKeyValueTagsInput!) {
                  updateKeyValueTags(input: $input) {
                    tagUri
                    targetUri
                    targetType
                    key
                    value
                    cascade
                  }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.updateKeyValueTags
