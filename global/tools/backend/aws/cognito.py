import logging
import boto3

from .sts import SessionHelper


log = logging.getLogger(__name__)


class Cognito:
    @staticmethod
    def client(account_id: str, region_name: str, client_type: str):
        session = SessionHelper.remote_session(account_id)
        return session.client(client_type, region_name=region_name)

    @staticmethod
    def list_cognito_groups(envname: str, region: str):
        try:
            parameter_path = f'/dataall/{envname}/cognito/userpool'
            ssm = boto3.client('ssm', region_name=region)
            user_pool_id = ssm.get_parameter(Name=parameter_path)['Parameter']['Value']
            cognito = boto3.client('cognito-idp', region_name=region)
            groups = cognito.list_groups(UserPoolId=user_pool_id)['Groups']
        except Exception as e:
            log.error(
                f'Failed to list groups of user pool {user_pool_id} due to {e}'
            )
        else:
            return groups
