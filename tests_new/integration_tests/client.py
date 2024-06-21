import requests
import boto3
import os
from munch import DefaultMunch

from integration_tests.errors import GqlError

ENVNAME = os.getenv('ENVNAME', 'dev')


class Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = self._get_jwt_token()

    def query(self, query: str):
        graphql_endpoint = os.path.join(os.environ['API_ENDPOINT'], 'graphql', 'api')
        headers = {'AccessKeyId': 'none', 'SecretKey': 'none', 'authorization': self.token}
        r = requests.post(graphql_endpoint, json=query, headers=headers)
        r.raise_for_status()
        if errors := r.json().get('errors'):
            raise GqlError(errors)

        return DefaultMunch.fromDict(r.json())

    def _get_jwt_token(self):
        cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        kwargs = {
            'ClientId': os.environ['COGNITO_CLIENT'],
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': self.username,
                'PASSWORD': self.password,
            },
        }
        resp = cognito_client.initiate_auth(**kwargs)

        return resp['AuthenticationResult']['IdToken']
