import logging
import json


from ....db import models, api
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.s3 import S3
from ....aws.handlers.kms import KMS
from ....aws.handlers.iam import IAM

from ....utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class S3ShareRevoke:
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        rejected_folders: [models.DatasetTable],
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ):
        self.session = session
        self.source_env_group = source_env_group
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.rejected_folders = rejected_folders
        self.source_environment = source_environment
        self.target_environment = target_environment

    def revoke_share(
            self,
    ) -> bool:
        """
        1) Shares folders, for each shared folder:
            a) ....
        2) Cleans un-shared folders

        Returns
        -------
        True if share is approved successfully
        """
        self.revoke_shared_folders(
            self.session,
            self.share,
            self.source_env_group,
            self.env_group,
            self.target_environment,
            self.rejected_folders,
            self.dataset,
        )

        return True

    @classmethod
    def revoke_shared_folders(
        cls,
        session,
        share: models.ShareObject,
        source_env_group: models.EnvironmentGroup,
        target_env_group: models.EnvironmentGroup,
        target_environment: models.Environment,
        rejected_folders: [models.DatasetStorageLocation],
        dataset: models.Dataset,
    ):
        for folder in rejected_folders:
            rejected_item = api.ShareObject.find_share_item_by_folder(
                session, share, folder
            )

            api.ShareObject.update_share_item_status(
                session,
                rejected_item,
                models.ShareObjectStatus.Revoke_In_Progress.value
            )

            source_account_id = folder.AWSAccountId
            access_point_name = rejected_item.S3AccessPointName
            bucket_name = folder.S3BucketName
            target_account_id = target_environment.AwsAccountId
            target_env_admin = target_env_group.environmentIAMRoleName
            s3_prefix = folder.S3Prefix

            try:
                S3ShareRevoke.delete_access_point_policy(
                    source_account_id,
                    target_account_id,
                    access_point_name,
                    target_env_admin,
                    s3_prefix,
                )
                cleanup = S3ShareRevoke.delete_access_point(source_account_id, access_point_name)
                if cleanup:
                    S3ShareRevoke.delete_target_role_access_policy(
                        target_account_id,
                        target_env_admin,
                        bucket_name,
                        access_point_name,
                        dataset,
                    )
                    S3ShareRevoke.delete_dataset_bucket_key_policy(
                        source_account_id,
                        target_account_id,
                        target_env_admin,
                        dataset,
                    )
                api.ShareObject.update_share_item_status(
                    session,
                    rejected_item,
                    models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                )
            except Exception as e:
                S3ShareRevoke.handle_share_failure(folder, rejected_item, e)

    @staticmethod
    def delete_access_point_policy(
        source_account_id: str,
        target_account_id: str,
        access_point_name: str,
        target_env_admin: str,
        s3_prefix: str,
    ):
        access_point_policy = json.loads(S3.get_access_point_policy(source_account_id, access_point_name))
        access_point_arn = S3.get_bucket_access_point_arn(source_account_id, access_point_name)
        target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
        statements = {item["Sid"]: item for item in access_point_policy["Statement"]}
        if f"{target_env_admin_id}0" in statements.keys():
            prefix_list = statements[f"{target_env_admin_id}0"]["Condition"]["StringLike"]["s3:prefix"]
            if isinstance(prefix_list, list) and f"{s3_prefix}/*" in prefix_list:
                prefix_list.remove(f"{s3_prefix}/*")
                statements[f"{target_env_admin_id}1"]["Resource"].remove(f"{access_point_arn}/object/{s3_prefix}/*")
                access_point_policy["Statement"] = list(statements.values())
            else:
                access_point_policy["Statement"].remove(statements[f"{target_env_admin_id}0"])
                access_point_policy["Statement"].remove(statements[f"{target_env_admin_id}1"])
        S3.attach_access_point_policy(source_account_id, access_point_name, json.dumps(access_point_policy))

    @staticmethod
    def delete_access_point(source_account_id: str, access_point_name: str):
        access_point_policy = json.loads(S3.get_access_point_policy(source_account_id, access_point_name))
        if len(access_point_policy["Statement"]) <= 1:
            # At least we have the 'AllowAllToAdmin' statement
            S3.delete_bucket_access_point(source_account_id, access_point_name)
            return True
        else:
            return False

    @staticmethod
    def delete_target_role_access_policy(
        target_account_id: str,
        target_env_admin: str,
        bucket_name: str,
        access_point_name: str,
        dataset: models.Dataset,
    ):
        existing_policy = IAM.get_role_policy(
            target_account_id,
            target_env_admin,
            "targetDatasetAccessControlPolicy",
        )
        if existing_policy:
            if bucket_name in ",".join(existing_policy["Statement"][0]["Resource"]):
                target_resources = [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*",
                    f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}",
                    f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}/*"
                ]
                for item in target_resources:
                    existing_policy["Statement"][0]["Resource"].remove(item)
                if not existing_policy["Statement"][0]["Resource"]:
                    IAM.delete_role_policy(target_account_id, target_env_admin, "targetDatasetAccessControlPolicy")
                else:
                    IAM.update_role_policy(
                        target_account_id,
                        target_env_admin,
                        "targetDatasetAccessControlPolicy",
                        json.dumps(existing_policy),
                    )

    @staticmethod
    def delete_dataset_bucket_key_policy(
        source_account_id: str,
        target_account_id: str,
        target_env_admin: str,
        dataset: models.Dataset,
    ):
        key_alias = f"alias/{dataset.KmsAlias}"
        kms_keyId = KMS.get_key_id(source_account_id, key_alias)
        existing_policy = KMS.get_key_policy(source_account_id, kms_keyId, "default")
        target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
        if existing_policy and f'{target_env_admin_id}:*' in existing_policy:
            policy = json.loads(existing_policy)
            policy["Statement"] = [item for item in policy["Statement"] if item["Sid"] != f"{target_env_admin_id}"]
            KMS.put_key_policy(
                source_account_id,
                kms_keyId,
                "default",
                json.dumps(policy)
            )

    def handle_share_failure(
        self,
        folder: models.DatasetStorageLocation,
        share_item: models.ShareObjectItem,
        error: Exception,
    ) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Parameters
        ----------
        folder : dataset folder
        share_item : failed item
        error : share error

        Returns
        -------
        True if alarm published successfully
        """
        logging.error(
            f'Failed to revoke S3 permissions to folder {folder.S3Prefix} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region}'
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            share_item,
            models.ShareObjectStatus.Revoke_Share_Failed.value,
        )
        AlarmService().trigger_revoke_folder_sharing_failure_alarm(
            folder, self.share, self.target_environment
        )
        return True
