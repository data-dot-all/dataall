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
            log.info(
                f'Created managed policy {arn}'
            )
            return arn
        except Exception as e:
            log.error(
                f'Failed to create managed policy {policy_name} : {e}'
            )
            return None

    @staticmethod
    def delete_managed_policy_by_name(
            account_id: str,
            policy_name):
        try:
            arn = f'arn:aws:iam::{account_id}:policy/{policy_name}'
            iamcli = IAM.client(account_id)
            iamcli.delete_policy(
                PolicyArn=arn
            )
        except Exception as e:
            log.error(
                f'Failed to delete managed policy {policy_name} : {e}'
            )

    @staticmethod
    def get_managed_policy_default_version(
            account_id: str,
            policy_name: str):
        try:
            arn = f'arn:aws:iam::{account_id}:policy/{policy_name}'
            iamcli = IAM.client(account_id)
            response = iamcli.get_policy(PolicyArn=arn)
            versionId = response['Policy']['DefaultVersionId']
            policyVersion = iamcli.get_policy_version(PolicyArn=arn, VersionId=versionId)
            policyDocument = policyVersion['PolicyVersion']['Document']
            return versionId, policyDocument
        except Exception as e:
            log.error(
                f'Failed to get policy {policy_name} : {e}'
            )
            return None

    @staticmethod
    def update_managed_policy_default_version(
            account_id: str,
            policy_name: str,
            old_version_id: str,
            policy_document: str):
        try:
            arn = f'arn:aws:iam::{account_id}:policy/{policy_name}'
            iamcli = IAM.client(account_id)
            iamcli.create_policy_version(
                PolicyArn=arn,
                PolicyDocument=policy_document,
                SetAsDefault=True
            )

            iamcli.delete_policy_version(PolicyArn=arn, VersionId=old_version_id)
        except Exception as e:
            log.error(
                f'Failed to update policy {policy_name} : {e}'
            )

    @staticmethod
    def detach_policy_from_role(
            account_id: str,
            role_name: str,
            policy_name: str):

        try:
            arn = f'arn:aws:iam::{account_id}:policy/{policy_name}'
            iamcli = IAM.client(account_id)
            iamcli.detach_role_policy(
                RoleName=role_name,
                PolicyArn=arn
            )
        except Exception as e:
            log.error(
                f'Failed to detach policy {policy_name} from role {role_name} : {e}'
            )

    @staticmethod
    def get_policy_by_name(
            account_id: str,
            policy_name: str
    ):
        try:
            arn = f'arn:aws:iam::{account_id}:policy/{policy_name}'
            iamcli = IAM.client(account_id)
            response = iamcli.get_policy(PolicyArn=arn)
            return response['Policy']
        except Exception as e:
            log.error(
                f'Failed to get policy {policy_name} : {e}'
            )
            return None
