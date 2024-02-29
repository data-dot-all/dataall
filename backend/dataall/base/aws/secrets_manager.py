import logging
import os

import boto3
from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)

_DEFAULT_REGION = os.environ.get('AWS_REGION', 'eu-west-1')


class SecretsManager:
    def __init__(self, account_id=None, region=_DEFAULT_REGION):
        if account_id:
            session = SessionHelper.remote_session(account_id, region)
            self._client = session.client('secretsmanager', region_name=region)
        else:
            self._client = boto3.client('secretsmanager', region_name=region)

    def get_secret_value(self, secret_id):
        if not secret_id:
            raise Exception('Secret name is None')
        try:
            secret_value = self._client.get_secret_value(SecretId=secret_id)['SecretString']
        except ClientError as e:
            raise Exception(e)
        return secret_value
