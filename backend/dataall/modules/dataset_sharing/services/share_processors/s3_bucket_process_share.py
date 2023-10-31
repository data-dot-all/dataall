import logging

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.services.share_managers import S3BucketShareManager
from dataall.modules.datasets_base.db.dataset_models import Dataset, DatasetBucket
from dataall.modules.dataset_sharing.db.enums import ShareItemStatus, ShareObjectActions, ShareItemActions
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository, ShareItemSM


log = logging.getLogger(__name__)


class ProcessS3BucketShare(S3BucketShareManager):
    def __init__(
        self,
        session,
        dataset: Dataset,
        share: ShareObject,
        s3_bucket: DatasetBucket,
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup,
    ):

        super().__init__(
            session,
            dataset,
            share,
            s3_bucket,
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
        shared_buckets: [DatasetBucket],
        source_environment: Environment,
        target_environment: Environment,
        source_env_group: EnvironmentGroup,
        env_group: EnvironmentGroup
    ) -> bool:
        """
        1) update_share_item_status with Start action
        2) manage_bucket_policy - grants permission in the bucket policy
        3) grant_target_role_access_policy == done
        4) update_dataset_bucket_key_policy == done
        5) update_share_item_status with Finish action == done

        Returns
        -------
        True if share is granted successfully
        """
        log.info(
            '##### Starting S3 bucket share #######'
        )
        success = True
        for shared_bucket in shared_buckets:
            sharing_item = ShareObjectRepository.find_sharable_item(
                session,
                share.shareUri,
                shared_bucket.bucketUri,
            )
            shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
            new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
            shared_item_SM.update_state_single_item(session, sharing_item, new_state)

            sharing_bucket = cls(
                session,
                dataset,
                share,
                shared_bucket,
                source_environment,
                target_environment,
                source_env_group,
                env_group
            )
            try:
                sharing_bucket.grant_role_bucket_policy()
                sharing_bucket.grant_s3_iam_access()
                sharing_bucket.grant_dataset_bucket_key_policy()
                new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                shared_item_SM.update_state_single_item(session, sharing_item, new_state)

            except Exception as e:
                sharing_bucket.handle_share_failure(e)
                new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                shared_item_SM.update_state_single_item(session, sharing_item, new_state)
                success = False
        return success

    @classmethod
    def process_revoked_shares(
            cls,
            session,
            dataset: Dataset,
            share: ShareObject,
            revoked_buckets: [DatasetBucket],
            source_environment: Environment,
            target_environment: Environment,
            source_env_group: EnvironmentGroup,
            env_group: EnvironmentGroup,
            existing_shared_folders: bool = False
    ) -> bool:
        """
        1) update_share_item_status with Start action
        2) remove access from bucket policy
        3) remove access from key policy
        4) remove access from IAM role policy
        5) update_share_item_status with Finish action

        Returns
        -------
        True if share is revoked successfully
        False if revoke fails
        """

        log.info(
            '##### Starting Revoking S3 bucket share #######'
        )
        success = True
        for revoked_bucket in revoked_buckets:
            removing_item = ShareObjectRepository.find_sharable_item(
                session,
                share.shareUri,
                revoked_bucket.bucketUri,
            )

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(session, removing_item, new_state)
            removing_bucket = cls(
                session,
                dataset,
                share,
                revoked_bucket,
                source_environment,
                target_environment,
                source_env_group,
                env_group
            )
            try:
                removing_bucket.delete_target_role_bucket_policy()
                removing_bucket.delete_target_role_access_policy(
                    share=share,
                    target_bucket=revoked_bucket,
                    target_environment=target_environment
                )
                if not existing_shared_folders:
                    removing_bucket.delete_target_role_bucket_key_policy(
                        share=share,
                        target_bucket=revoked_bucket,
                        target_environment=target_environment
                    )
                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(session, removing_item, new_state)

            except Exception as e:
                removing_bucket.handle_revoke_failure(e)
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(session, removing_item, new_state)
                success = False

        return success
