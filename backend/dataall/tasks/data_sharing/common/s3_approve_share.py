import logging

from ....db import models, api
from .s3_share_manager import S3ShareManager


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
        revoke_folders: [models.DatasetStorageLocation],
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
            log.info(f'sharing folder: {folder}')
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

        for folder in revoke_folders:
            log.info(f'revoking access to folder: {folder}')
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
                api.ShareObject.update_share_item_status(
                    session,
                    removing_item,
                    models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                )
            except Exception as e:
                removing_folder.handle_revoke_failure(e)
        return True
