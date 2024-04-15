import logging
from datetime import datetime

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.dataset_sharing.services.share_managers import S3AccessPointShareManager
from dataall.modules.dataset_sharing.services.share_object_service import ShareObjectService
from dataall.modules.datasets.db.dataset_models import DatasetStorageLocation, Dataset
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (
    ShareItemHealthStatus,
    ShareItemStatus,
    ShareObjectActions,
    ShareItemActions,
)
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository, ShareItemSM


log = logging.getLogger(__name__)


class ProcessS3AccessPointShare(S3AccessPointShareManager):
    def __init__(
        self,
        session,
        dataset: Dataset,
        share: ShareObject,
        share_folder: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup,
        existing_shared_buckets: bool = False,
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
    def process_approved_shares(
        cls,
        session,
        dataset: Dataset,
        share: ShareObject,
        share_folders: [DatasetStorageLocation],
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup,
        reapply: bool = False,
    ) -> bool:
        """
        1) update_share_item_status with Start action
        2) (one time only) manage_bucket_policy - grants permission in the bucket policy
        3) grant_target_role_access_policy
        4) manage_access_point_and_policy
        5) update_dataset_bucket_key_policy
        6) update_share_item_status with Finish action

        Returns
        -------
        True if share is granted successfully
        """
        log.info('##### Starting Sharing folders #######')
        success = True
        for folder in share_folders:
            log.info(f'sharing folder: {folder}')
            sharing_item = ShareObjectRepository.find_sharable_item(
                session,
                share.shareUri,
                folder.locationUri,
            )
            if not reapply:
                shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                shared_item_SM.update_state_single_item(session, sharing_item, new_state)

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
                if not ShareObjectService.verify_principal_role(session, share):
                    raise PrincipalRoleNotFound(
                        'process approved shares',
                        f'Principal role {share.principalIAMRoleName} is not found. Failed to update bucket policy',
                    )

                sharing_folder.manage_bucket_policy()
                sharing_folder.grant_target_role_access_policy()
                sharing_folder.manage_access_point_and_policy()
                if not dataset.imported or dataset.importedKmsKey:
                    sharing_folder.update_dataset_bucket_key_policy()

                if not reapply:
                    new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                    shared_item_SM.update_state_single_item(session, sharing_item, new_state)
                ShareObjectRepository.update_share_item_health_status(
                    session, sharing_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                )

            except Exception as e:
                # must run first to ensure state transitions to failed
                if not reapply:
                    new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                    shared_item_SM.update_state_single_item(session, sharing_item, new_state)
                else:
                    ShareObjectRepository.update_share_item_health_status(
                        session, sharing_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                    )
                success = False
                sharing_folder.handle_share_failure(e)
        return success

    @classmethod
    def process_revoked_shares(
        cls,
        session,
        dataset: Dataset,
        share: ShareObject,
        revoke_folders: [DatasetStorageLocation],
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup,
    ) -> bool:
        """
        1) update_share_item_status with Start action
        2) delete_access_point_policy for folder
        3) update_share_item_status with Finish action

        Returns
        -------
        True if share is revoked successfully
        """

        log.info('##### Starting Revoking folders #######')
        success = True
        for folder in revoke_folders:
            log.info(f'revoking access to folder: {folder}')
            removing_item = ShareObjectRepository.find_sharable_item(
                session,
                share.shareUri,
                folder.locationUri,
            )

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(session, removing_item, new_state)

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
                access_point_policy = removing_folder.revoke_access_in_access_point_policy()

                if len(access_point_policy['Statement']) > 0:
                    removing_folder.attach_new_access_point_policy(access_point_policy)
                else:
                    log.info('Cleaning up folder share resources...')
                    removing_folder.delete_access_point()
                    removing_folder.revoke_target_role_access_policy()
                    if not dataset.imported or dataset.importedKmsKey:
                        removing_folder.delete_dataset_bucket_key_policy(dataset=dataset)
                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(session, removing_item, new_state)
                ShareObjectRepository.update_share_item_health_status(
                    session, removing_item, None, None, removing_item.lastVerificationTime
                )

            except Exception as e:
                # must run first to ensure state transitions to failed
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(session, removing_item, new_state)
                success = False

                # statements which can throw exceptions but are not critical
                removing_folder.handle_revoke_failure(e)

        return success

    @classmethod
    def verify_shares(
        cls,
        session,
        dataset: Dataset,
        share: ShareObject,
        share_folders: [DatasetStorageLocation],
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup,
    ) -> bool:
        log.info('##### Verifying folders shares #######')
        for folder in share_folders:
            sharing_item = ShareObjectRepository.find_sharable_item(
                session,
                share.shareUri,
                folder.locationUri,
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
                sharing_folder.check_bucket_policy()
                sharing_folder.check_target_role_access_policy()
                sharing_folder.check_access_point_and_policy()

                if not dataset.imported or dataset.importedKmsKey:
                    sharing_folder.check_dataset_bucket_key_policy()
            except Exception as e:
                sharing_folder.folder_errors = [str(e)]

            if len(sharing_folder.folder_errors):
                ShareObjectRepository.update_share_item_health_status(
                    sharing_folder.session,
                    sharing_item,
                    ShareItemHealthStatus.Unhealthy.value,
                    ' | '.join(sharing_folder.folder_errors),
                    datetime.now(),
                )
            else:
                ShareObjectRepository.update_share_item_health_status(
                    sharing_folder.session, sharing_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                )
        return True
