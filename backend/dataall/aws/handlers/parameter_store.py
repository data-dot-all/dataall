import logging

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)


def ns2d(**kwargs):
    return kwargs


class ParameterStoreManager:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('ssm', region_name=region)

    @staticmethod
    def get_parameter_value(AwsAccountId, region, parameter_path):
        if not parameter_path:
            raise Exception('Secret name is None')
        try:
            parameter_value = ParameterStoreManager.client(
                AwsAccountId, region
            ).get_parameter(Name=parameter_path)['Parameter']['Value']
        except ClientError as e:
            raise Exception(e)
        return parameter_value
