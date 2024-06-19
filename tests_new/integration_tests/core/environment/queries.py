def create_environment(client, name, group, organizationUri, awsAccountId, region):
    query = {
        'operationName': 'CreateEnvironment',
        'variables': {
            'input': {
                'label': name,
                'SamlGroupName': group,
                'organizationUri': organizationUri,
                'AwsAccountId': awsAccountId,
                'region': region,
                'description': 'Created for integration testing',
                'tags': [],
            }
        },
        'query': """
                    mutation CreateEnvironment($input: NewEnvironmentInput) {
                      createEnvironment(input: $input) {
                        environmentUri
                        label
                        userRoleInEnvironment
                        SamlGroupName
                        AwsAccountId
                        created
                        parameters {
                          key
                          value
                        }
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.createEnvironment


def get_environment(client, environmentUri):
    query = {
        'operationName': 'GetEnvironment',
        'variables': {'environmentUri': environmentUri},
        'query': """
                    query GetEnvironment($environmentUri: String) {
                      getEnvironment(environmentUri: $environmentUri) {
                        environmentUri
                        created
                        userRoleInEnvironment
                        description
                        name
                        label
                        AwsAccountId
                        region
                        owner
                        tags
                        SamlGroupName
                        EnvironmentDefaultBucketName
                        EnvironmentDefaultIAMRoleArn
                        EnvironmentDefaultIAMRoleName
                        EnvironmentDefaultIAMRoleImported
                        resourcePrefix
                        subscriptionsEnabled
                        subscriptionsProducersTopicImported
                        subscriptionsConsumersTopicImported
                        subscriptionsConsumersTopicName
                        subscriptionsProducersTopicName
                        organization {
                          organizationUri
                          label
                          name
                        }
                        stack {
                          stack
                          status
                          stackUri
                          targetUri
                          accountid
                          region
                          stackid
                          link
                          outputs
                          resources
                        }
                        networks {
                          VpcId
                          privateSubnetIds
                          publicSubnetIds
                        }
                        parameters {
                          key
                          value
                        }
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.getEnvironment


def delete_environment(client, environmentUri, deleteFromAWS=True):
    query = {
        'operationName': 'deleteEnvironment',
        'variables': {
            'environmentUri': environmentUri,
            'deleteFromAWS': deleteFromAWS,
        },
        'query': """
                    mutation deleteEnvironment(
                      $environmentUri: String!
                      $deleteFromAWS: Boolean
                    ) {
                      deleteEnvironment(
                        environmentUri: $environmentUri
                        deleteFromAWS: $deleteFromAWS
                      )
                    }
                """,
    }
    response = client.query(query=query)
    return response
