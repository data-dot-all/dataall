import logging
from datetime import datetime
from typing import List

from dataall.modules.s3_datasets_shares.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.s3_datasets_shares.services.share_managers import S3AccessPointShareManager
from dataall.modules.s3_datasets_shares.services.share_object_service import ShareObjectService
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareItemStatus,
    ShareObjectActions,
    ShareItemActions,
)

from dataall.modules.s3_datasets_shares.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import ShareItemSM
from dataall.modules.shares_base.services.sharing_service import SharesProcessorInterface


log = logging.getLogger(__name__)


class ProcessS3AccessPointShare(SharesProcessorInterface):
    @staticmethod
    def initialize_share_manager(
        session, dataset, share, items, source_environment, target_environment, env_group, reapply=False
    ) -> List[S3AccessPointShareManager]:
        managers = []
        for folder in items:
            managers.append(
                S3AccessPointShareManager(
                    session, dataset, share, folder, source_environment, target_environment, env_group, reapply
                )
            )
        return managers

    @staticmethod
    def process_approved_shares(share_manager: List[S3AccessPointShareManager]) -> bool:
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
        for manager in share_manager:
            log.info(f'sharing folder: {manager.target_folder}')
            sharing_item = ShareObjectRepository.find_sharable_item(
                manager.session,
                manager.share.shareUri,
                manager.target_folder.locationUri,
            )
            if not manager.reapply:
                shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                shared_item_SM.update_state_single_item(manager.session, sharing_item, new_state)

            try:
                if not ShareObjectService.verify_principal_role(manager.session, manager.share):
                    raise PrincipalRoleNotFound(
                        'process approved shares',
                        f'Principal role {manager.share.principalIAMRoleName} is not found. Failed to update bucket policy',
                    )

                manager.manage_bucket_policy()
                manager.grant_target_role_access_policy()
                manager.manage_access_point_and_policy()
                if not manager.dataset.imported or manager.dataset.importedKmsKey:
                    manager.update_dataset_bucket_key_policy()

                if not manager.reapply:
                    new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                    shared_item_SM.update_state_single_item(manager.session, sharing_item, new_state)
                ShareObjectRepository.update_share_item_health_status(
                    manager.session, sharing_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                )

            except Exception as e:
                # must run first to ensure state transitions to failed
                if not manager.reapply:
                    new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                    shared_item_SM.update_state_single_item(manager.session, sharing_item, new_state)
                else:
                    ShareObjectRepository.update_share_item_health_status(
                        manager.session, sharing_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                    )
                success = False
                manager.handle_share_failure(e)
        return success

    @staticmethod
    def process_revoked_shares(share_manager: List[S3AccessPointShareManager]) -> bool:
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
        for manager in share_manager:
            log.info(f'revoking access to folder: {manager.target_folder}')
            removing_item = ShareObjectRepository.find_sharable_item(
                manager.session,
                manager.share.shareUri,
                manager.target_folder.locationUri,
            )

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(manager.session, removing_item, new_state)

            try:
                access_point_policy = manager.revoke_access_in_access_point_policy()

                if len(access_point_policy['Statement']) > 0:
                    manager.attach_new_access_point_policy(access_point_policy)
                else:
                    log.info('Cleaning up folder share resources...')
                    manager.delete_access_point()
                    manager.revoke_target_role_access_policy()
                    if not manager.dataset.imported or manager.dataset.importedKmsKey:
                        manager.delete_dataset_bucket_key_policy(dataset=manager.dataset)
                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(manager.session, removing_item, new_state)
                ShareObjectRepository.update_share_item_health_status(
                    manager.session, removing_item, None, None, removing_item.lastVerificationTime
                )

            except Exception as e:
                # must run first to ensure state transitions to failed
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(manager.session, removing_item, new_state)
                success = False

                # statements which can throw exceptions but are not critical
                manager.handle_revoke_failure(e)

        return success

    @staticmethod
    def verify_shares(share_manager: List[S3AccessPointShareManager]) -> bool:
        log.info('##### Verifying folders shares #######')
        for manager in share_manager:
            sharing_item = ShareObjectRepository.find_sharable_item(
                manager.session,
                manager.share.shareUri,
                manager.target_folder.locationUri,
            )

            try:
                manager.check_bucket_policy()
                manager.check_target_role_access_policy()
                manager.check_access_point_and_policy()

                if not manager.dataset.imported or manager.dataset.importedKmsKey:
                    manager.check_dataset_bucket_key_policy()
            except Exception as e:
                manager.folder_errors = [str(e)]

            if len(manager.folder_errors):
                ShareObjectRepository.update_share_item_health_status(
                    manager.session,
                    sharing_item,
                    ShareItemHealthStatus.Unhealthy.value,
                    ' | '.join(manager.folder_errors),
                    datetime.now(),
                )
            else:
                ShareObjectRepository.update_share_item_health_status(
                    manager.session, sharing_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                )
        return True
