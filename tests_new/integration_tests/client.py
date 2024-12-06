import logging
import os
import uuid
from pprint import pformat
from urllib.parse import parse_qs, urlparse

import requests
from munch import DefaultMunch
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from retrying import retry

from integration_tests.errors import GqlError

ENVNAME = os.getenv('ENVNAME', 'dev')


def _retry_if_connection_error(exception):
    """Return True if we should retry, False otherwise"""
    return isinstance(exception, requests.exceptions.ConnectionError) or isinstance(exception, requests.ReadTimeout)


class Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token = self._get_jwt_tokens()

    @retry(
        retry_on_exception=_retry_if_connection_error,
        stop_max_attempt_number=3,
        wait_random_min=1000,
        wait_random_max=3000,
    )
    def query(self, query: dict):
        graphql_endpoint = os.path.join(os.environ['API_ENDPOINT'], 'graphql', 'api')
        headers = {'accesskeyid': 'none', 'SecretKey': 'none', 'Authorization': f'Bearer {self.access_token}'}
        r = requests.post(graphql_endpoint, json=query, headers=headers)
        response = r.json()
        if errors := response.get('errors'):
            if any((response.get('data', {}) or {}).values()):  # check if there are data
                logging.warning(f'{query=} returned both data and errors:\n {pformat(response)}')
            else:
                raise GqlError(errors)
        r.raise_for_status()
        return DefaultMunch.fromDict(response)

    def _get_jwt_tokens(self):
        token = uuid.uuid4()
        scope = 'aws.cognito.signin.user.admin openid'

        idp_domain_url = os.environ['IDP_DOMAIN_URL']

        token_url = os.path.join(idp_domain_url, 'oauth2', 'token')
        login_url = os.path.join(idp_domain_url, 'login')

        client_id = os.environ['COGNITO_CLIENT']
        redirect_uri = os.environ['DATAALL_DOMAIN_URL']

        data = {
            '_csrf': token,
            'username': self.username,
            'password': self.password,
        }
        params = {
            'client_id': client_id,
            'scope': scope,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
        }

        headers = {'cookie': f'XSRF-TOKEN={token}; csrf-state=""; csrf-state-legacy=""'}
        r = requests.post(
            login_url,
            params=params,
            data=data,
            headers=headers,
            allow_redirects=False,
        )

        r.raise_for_status()

        code = parse_qs(urlparse(r.headers['location']).query)['code'][0]

        client = WebApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client, redirect_uri=redirect_uri)
        token = oauth.fetch_token(
            token_url=token_url,
            client_id=client_id,
            code=code,
            include_client_id=True,
        )

        return token.get('access_token')
