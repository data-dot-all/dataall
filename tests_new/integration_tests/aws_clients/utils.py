import json
import boto3

from tests_new.integration_tests.aws_clients.sts import StsClient


# it's here and not in Env test module, because it's used only here and we don't want circular dependencies
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


def get_group_session(client, env_uri, group):
    credentials = json.loads(get_environment_access_token(client, env_uri, group))

    return boto3.Session(
        aws_access_key_id=credentials['AccessKey'],
        aws_secret_access_key=credentials['SessionKey'],
        aws_session_token=credentials['sessionToken'],
    )


def get_role_session(session, role_arn, region):
    sts_client = StsClient(session=session, region=region)
    return sts_client.get_role_session(role_arn)
