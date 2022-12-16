import logging

from .sts import SessionHelper


log = logging.getLogger(__name__)


class IAM:
    @staticmethod
    def client(account_id: str):
        session = SessionHelper.remote_session(account_id)
        return session.client('iam')

    @staticmethod
    def get_role(
        account_id: str,
        role_arn: str
    ):
        try:
            iamcli = IAM.client(account_id)
            response = iamcli.get_role(
                RoleName=role_arn.split("/")[-1]
            )
        except Exception as e:
            log.error(
                f'Failed to get role {role_arn} due to: {e}'
            )
            return None
        else:
            return response["Role"]

    @staticmethod
    def update_role_policy(
        account_id: str,
        role_name: str,
        policy_name: str,
        policy: str,
    ):
        try:
            iamcli = IAM.client(account_id)
            iamcli.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=policy,
            )
        except Exception as e:
            log.error(
                f'Failed to add S3 bucket access to target role {account_id}/{role_name} : {e}'
            )
            raise e

    @staticmethod
    def get_role_policy(
        account_id: str,
        role_name: str,
        policy_name: str,
    ):
        try:
            iamcli = IAM.client(account_id)
            response = iamcli.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
            )
        except Exception as e:
            log.error(
                f'Failed to get policy {policy_name} of role {role_name} : {e}'
            )
            return None
        else:
            return response["PolicyDocument"]

    @staticmethod
    def delete_role_policy(
        account_id: str,
        role_name: str,
        policy_name: str,
    ):
        try:
            iamcli = IAM.client(account_id)
            iamcli.delete_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
            )
        except Exception as e:
            log.error(
                f'Failed to delete policy {policy_name} of role {role_name} : {e}'
            )
