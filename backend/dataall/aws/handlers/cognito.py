import logging

from .sts import SessionHelper


log = logging.getLogger(__name__)


class Cognito:
    @staticmethod
    def client(account_id: str, region_name: str, client_type: str):
        session = SessionHelper.remote_session(account_id)
        return session.client(client_type, region_name=region_name)

    @staticmethod
    def list_cognito_groups(account_id: str, region: str, user_pool_id: str):
        try:
            cognitoCli = Cognito.client(account_id, region, "cognito-idp")
            response = cognitoCli.list_groups(UsePoolId=user_pool_id)
        except Exception as e:
            log.error(
                f'Failed to list groups of user pool {user_pool_id} due to {e}'
            )
        else:
            return response['Groups']
