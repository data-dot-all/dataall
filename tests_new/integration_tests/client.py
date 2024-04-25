import requests
import boto3
import os
from munch import DefaultMunch
from dataall.base.aws.parameter_store import ParameterStoreManager


ENVNAME = os.getenv('ENVNAME', 'dev')


class Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = self._get_jwt_token()

    def query(self, query: str):
        endpoint = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'), parameter_path=f'/dataall/{ENVNAME}/apiGateway/backendUrl'
        )
        graphql_endpoint = f'{endpoint}graphql/api'
        headers = {'AccessKeyId': 'none', 'SecretKey': 'none', 'authorization': self.token}
        r = requests.post(graphql_endpoint, json=query, headers=headers)
        r.raise_for_status()

        return DefaultMunch.fromDict(r.json())

    def _get_jwt_token(self):
        cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        client_id = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'), parameter_path=f'/dataall/{ENVNAME}/cognito/appclient'
        )
        kwargs = {
            'ClientId': client_id,
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': self.username,
                'PASSWORD': self.password,
            },
        }
        resp = cognito_client.initiate_auth(**kwargs)

        return resp['AuthenticationResult']['IdToken']
