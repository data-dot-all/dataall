ENV_TYPE = """
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
EnvironmentLogsBucketName
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
  updated
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
"""


def create_environment(client, name, group, organizationUri, awsAccountId, region, tags):
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
                'tags': tags,
                'type': 'IntegrationTesting',
                'parameters': [],
            }
        },
        'query': f"""
                    mutation CreateEnvironment($input: NewEnvironmentInput!) {{
                      createEnvironment(input: $input) {{
                        {ENV_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createEnvironment


def get_environment(client, environmentUri):
    query = {
        'operationName': 'GetEnvironment',
        'variables': {'environmentUri': environmentUri},
        'query': f"""
                    query GetEnvironment($environmentUri: String!) {{
                      getEnvironment(environmentUri: $environmentUri) {{
                        {ENV_TYPE}  
                      }}
                    }}
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


def update_environment(client, environmentUri, input: dict):
    query = {
        'operationName': 'UpdateEnvironment',
        'variables': {
            'environmentUri': environmentUri,
            'input': input,
        },
        'query': f"""
                    mutation UpdateEnvironment(
                      $environmentUri: String!
                      $input: ModifyEnvironmentInput!
                    ) {{
                      updateEnvironment(environmentUri: $environmentUri, input: $input) {{
                        {ENV_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateEnvironment


def list_environments(client, term=''):
    query = {
        'operationName': 'ListEnvironments',
        'variables': {
            'filter': {'term': term},
        },
        'query': f"""
                    query ListEnvironments($filter: EnvironmentFilter) {{
                      listEnvironments(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                            {ENV_TYPE}
                        }}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.listEnvironments


def invite_group_on_env(client, env_uri, group_uri, perms, iam_role_arn=None):
    query = {
        'operationName': 'inviteGroupOnEnvironment',
        'variables': {
            'input': {
                'environmentUri': env_uri,
                'groupUri': group_uri,
                'permissions': perms,
                'environmentIAMRoleArn': iam_role_arn,
            },
        },
        'query': """
                    mutation inviteGroupOnEnvironment($input: InviteGroupOnEnvironmentInput!) {
                      inviteGroupOnEnvironment(input: $input) {
                        environmentUri
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.inviteGroupOnEnvironment


def remove_group_from_env(client, env_uri, group_uri):
    query = {
        'operationName': 'removeGroupFromEnvironment',
        'variables': {'environmentUri': env_uri, 'groupUri': group_uri},
        'query': """
                    mutation removeGroupFromEnvironment(
                      $environmentUri: String!
                      $groupUri: String!
                    ) {
                      removeGroupFromEnvironment(
                        environmentUri: $environmentUri
                        groupUri: $groupUri
                      ) {
                        environmentUri
                      }
                    }
        """,
    }
    response = client.query(query=query)
    return response.data.removeGroupFromEnvironment


def add_consumption_role(client, env_uri, group_uri, consumption_role_name, iam_role_arn, is_managed=True):
    query = {
        'operationName': 'addConsumptionRoleToEnvironment',
        'variables': {
            'input': {
                'environmentUri': env_uri,
                'groupUri': group_uri,
                'consumptionRoleName': consumption_role_name,
                'IAMRoleArn': iam_role_arn,
                'dataallManaged': is_managed,
            },
        },
        'query': """
                    mutation addConsumptionRoleToEnvironment(
                      $input: AddConsumptionRoleToEnvironmentInput!
                    ) {
                      addConsumptionRoleToEnvironment(input: $input) {
                        consumptionRoleUri
                        consumptionRoleName
                        environmentUri
                        groupUri
                        IAMRoleArn
                      }
                    }
        """,
    }
    response = client.query(query=query)
    return response.data.addConsumptionRoleToEnvironment


def list_environment_consumption_roles(client, env_uri, filter):
    query = {
        'operationName': 'listEnvironmentConsumptionRoles',
        'variables': {'environmentUri': env_uri, 'filter': filter},
        'query': """
                    query listEnvironmentConsumptionRoles($environmentUri: String!, $filter: ConsumptionRoleFilter) {
                      listEnvironmentConsumptionRoles(environmentUri: $environmentUri, filter: $filter) {
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {
                          consumptionRoleUri
                          consumptionRoleName
                          environmentUri
                          groupUri
                          IAMRoleArn
                        }
                      }
                    }
        """,
    }
    response = client.query(query=query)
    return response.data.listEnvironmentConsumptionRoles


def remove_consumption_role(client, env_uri, consumption_role_uri):
    query = {
        'operationName': 'removeConsumptionRoleFromEnvironment',
        'variables': {
            'environmentUri': env_uri,
            'consumptionRoleUri': consumption_role_uri,
        },
        'query': """
                    mutation removeConsumptionRoleFromEnvironment(
                      $environmentUri: String!
                      $consumptionRoleUri: String!
                    ) {
                      removeConsumptionRoleFromEnvironment(
                        environmentUri: $environmentUri
                        consumptionRoleUri: $consumptionRoleUri
                      )
                    }
        """,
    }
    response = client.query(query=query)
    return response.data.removeConsumptionRoleFromEnvironment


def get_environment_access_token(client, env_uri, group_uri):
    query = {
        'operationName': 'generateEnvironmentAccessToken',
        'variables': {
            'environmentUri': env_uri,
            'groupUri': group_uri,
        },
        'query': """
                     query generateEnvironmentAccessToken(
                      $environmentUri: String!
                      $groupUri: String
                    ) {
                      generateEnvironmentAccessToken(
                        environmentUri: $environmentUri
                        groupUri: $groupUri
                      )
                    }
        """,
    }
    response = client.query(query=query)
    return response.data.generateEnvironmentAccessToken
