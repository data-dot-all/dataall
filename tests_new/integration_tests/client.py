import requests
import boto3
import os
from munch import DefaultMunch


ENVNAME = os.getenv('ENVNAME', 'dev')


class Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = self._get_jwt_token()

    def query(self, query: str):
        graphql_endpoint = f'{os.getenv("API_ENDPOINT", False)}graphql/api'
        headers = {'AccessKeyId': 'none', 'SecretKey': 'none', 'authorization': self.token}
        r = requests.post(graphql_endpoint, json=query, headers=headers)
        r.raise_for_status()

        return DefaultMunch.fromDict(r.json())

    def _get_jwt_token(self):
        cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        kwargs = {
            'ClientId': os.getenv('COGNITO_CLIENT', False),
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': self.username,
                'PASSWORD': self.password,
            },
        }
        resp = cognito_client.initiate_auth(**kwargs)

        return resp['AuthenticationResult']['IdToken']
