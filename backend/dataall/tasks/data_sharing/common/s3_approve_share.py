import logging
import json


from ....db import models, api
from .s3_share_manager import S3ShareManager
from ....aws.handlers.s3 import S3
from ....aws.handlers.sts import SessionHelper


log = logging.getLogger(__name__)


class S3ShareApproval(S3ShareManager):
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        share_folder: models.DatasetStorageLocation,
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ):

        super().__init__(
            session,
            dataset,
            share,
            share_folder,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

    @classmethod
    def approve_share(
        cls,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        share_folders: [models.DatasetStorageLocation],
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ) -> bool:
        """
        1) (one time only) manage_bucket_policy - grants permission in the bucket policy
        2) grant_target_role_access_policy
        3) manage_access_point_and_policy
        4) update_dataset_bucket_key_policy
        5) update_share_item_status

        Returns
        -------
        True if share is approved successfully
        """
        log.info(
            '##### Starting Sharing folders #######'
        )
        for folder in share_folders:
            sharing_item = api.ShareObject.find_share_item_by_folder(
                session,
                share,
                folder,
            )
            api.ShareObject.update_share_item_status(
                session,
                sharing_item,
                models.ShareObjectStatus.Share_In_Progress.value,
            )

            sharing_folder = cls(
                session,
                dataset,
                share,
                folder,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
            )

            try:
                sharing_folder.manage_bucket_policy()
                sharing_folder.grant_target_role_access_policy()
                sharing_folder.manage_access_point_and_policy()
                sharing_folder.update_dataset_bucket_key_policy()
                api.ShareObject.update_share_item_status(
                    session,
                    sharing_item,
                    models.ShareObjectStatus.Share_Succeeded.value,
                )
            except Exception as e:
                sharing_folder.handle_share_failure(e)

        removed_folders = S3ShareApproval.get_removed_prefixes(
            session,
            dataset,
            share,
            share_folders,
            target_environment,
            env_group,
        )
        for folder in removed_folders:
            removing_item = api.ShareObject.find_share_item_by_folder(
                session,
                share,
                folder,
            )
            api.ShareObject.update_share_item_status(
                session,
                removing_item,
                models.ShareObjectStatus.Revoke_In_Progress.value,
            )

            removing_folder = cls(
                session,
                dataset,
                share,
                folder,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
            )

            try:
                removing_folder.delete_access_point_policy()
                cleanup = removing_folder.delete_access_point()
                if cleanup:
                    removing_folder.delete_target_role_access_policy()
                    removing_folder.delete_dataset_bucket_key_policy()
            except Exception as e:
                removing_folder.handle_revoke_failure(e)
        return True

    @staticmethod
    def get_removed_prefixes(
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        share_folders: [models.DatasetStorageLocation],
        target_environment: models.Environment,
        env_group: models.EnvironmentGroup,
    ) -> [models.DatasetStorageLocation]:
        source_account_id = dataset.AwsAccountId
        access_point_name = f"{dataset.datasetUri}-{share.principalId}".lower()
        target_account_id = target_environment.AwsAccountId
        target_env_admin = env_group.environmentIAMRoleName
        access_point_policy = S3.get_access_point_policy(source_account_id, access_point_name)
        if access_point_policy:
            policy = json.loads(access_point_policy)
            target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
            statements = {item["Sid"]: item for item in policy["Statement"]}
            if f"{target_env_admin_id}0" in statements.keys():
                prefix_list = statements[f"{target_env_admin_id}0"]["Condition"]["StringLike"]["s3:prefix"]
                if isinstance(prefix_list, str):
                    prefix_list = [prefix_list]
                prefix_list = [prefix[:-2] for prefix in prefix_list]
                shared_prefix = [folder.S3Prefix for folder in share_folders]
                removed_prefixes = [prefix for prefix in prefix_list if prefix not in shared_prefix]
                removed_folders = [
                    api.DatasetStorageLocation.get_location_by_s3_prefix(
                        session,
                        prefix,
                        source_account_id,
                        dataset.region,
                    ) for prefix in removed_prefixes
                ]
                return removed_folders
