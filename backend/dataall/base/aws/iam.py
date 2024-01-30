import logging

from .sts import SessionHelper


log = logging.getLogger(__name__)


class IAM:
    @staticmethod
    def client(account_id: str, role=None):
        session = SessionHelper.remote_session(accountid=account_id, role=role)
        return session.client('iam')

    @staticmethod
    def get_role(account_id: str, role_arn: str, role=None):
        log.info(f"Getting IAM role = {role_arn}")
        try:
            iamcli = IAM.client(account_id=account_id, role=role)
            response = iamcli.get_role(
                RoleName=role_arn.split("/")[-1]
            )
            assert response['Role']['Arn'] == role_arn, "Arn doesn't match the role name. Check Arn and try again."
        except Exception as e:
            log.error(
                f'Failed to get role {role_arn} due to: {e}'
            )
            return None
        else:
            return response["Role"]

    @staticmethod
    def get_role_arn_by_name(account_id: str, role_name: str, role=None):
        log.info(f"Getting IAM role name= {role_name}")
        try:
            iamcli = IAM.client(account_id=account_id, role=role)
            response = iamcli.get_role(
                RoleName=role_name
            )
        except Exception as e:
            log.error(
                f'Failed to get role {role_name} due to: {e}'
            )
            return None
        else:
            return response["Role"]["Arn"]

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


    @staticmethod
    def create_managed_policy(
        account_id: str,
        policy_name: str,
        policy: str
    ):
        try:
            iamcli = IAM.client(account_id)
            response = iamcli.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy,
            )
            arn = response['Policy']['Arn']
            return arn
        except Exception as e:
            log.error(
                f'Failed to create managed policy {policy_name} : {e}'
            )
            return None

