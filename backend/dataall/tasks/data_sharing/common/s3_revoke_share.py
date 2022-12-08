import logging


from ....db import models, api
from .s3_share_manager import S3ShareManager


log = logging.getLogger(__name__)


class S3ShareRevoke(S3ShareManager):
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        revoke_folder: models.DatasetStorageLocation,
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ):
        super().__init__(
            session,
            dataset,
            share,
            revoke_folder,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

    @classmethod
    def revoke_share(
        cls,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        revoke_folders: [models.DatasetStorageLocation],
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ) -> bool:
        """
        1) Shares folders, for each shared folder:
            a) ....
        2) Cleans un-shared folders

        Returns
        -------
        True if share is approved successfully
        """
        log.info(
            '##### Starting Revoking folders #######'
        )
        for folder in revoke_folders:
            revoking_item = api.ShareObject.find_share_item_by_folder(
                session, share, folder
            )

            api.ShareObject.update_share_item_status(
                session,
                revoking_item,
                models.ShareObjectStatus.Revoke_In_Progress.value
            )
            revoking_folder = cls(
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
                revoking_folder.delete_access_point_policy()
                cleanup = revoking_folder.delete_access_point()
                if cleanup:
                    revoking_folder.delete_target_role_access_policy()
                    revoking_folder.delete_dataset_bucket_key_policy()
                api.ShareObject.update_share_item_status(
                    session,
                    revoking_item,
                    models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                )
            except Exception as e:
                revoking_folder.handle_revoke_failure(e)
        return True
