import logging

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)


def ns2d(**kwargs):
    return kwargs


class SecretsManager:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('secretsmanager', region_name=region)

    @staticmethod
    def get_secret_value(AwsAccountId, region, secretId):
        if not secretId:
            raise Exception('Secret name is None')
        try:
            secret_value = SecretsManager.client(
                AwsAccountId, region
            ).get_secret_value(SecretId=secretId)['SecretString']
        except ClientError as e:
            raise Exception(e)
        return secret_value
