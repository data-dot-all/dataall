import logging

from sqlalchemy import and_
from time import sleep
from datetime import datetime

from dataall.base.db import Engine
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectSM,
    ShareObjectRepository,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_processors.lakeformation_process_share import (
    ProcessLakeFormationShare,
)
from dataall.modules.dataset_sharing.services.share_processors.s3_access_point_process_share import (
    ProcessS3AccessPointShare,
)
from dataall.modules.dataset_sharing.services.share_processors.s3_bucket_process_share import ProcessS3BucketShare

from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (ShareItemHealthStatus, ShareObjectActions, ShareItemStatus, ShareableType)
from dataall.modules.datasets_base.db.dataset_models import DatasetLock


log = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_INTERVAL = 60


class DataSharingService:
    def __init__(self):
        pass

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Calls sharing folders processor to grant share
        4) Calls sharing buckets processor to grant share
        5) Calls sharing tables processor for same or cross account sharing to grant share
        6) Updates share object State Machine with the Action: Finish

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if sharing succeeds,
        False if folder or table sharing failed
        """
        try:
            with engine.scoped_session() as session:
                (
                    source_env_group,
                    env_group,
                    dataset,
                    share,
                    source_environment,
                    target_environment,
                ) = ShareObjectRepository.get_share_data(session, share_uri)

                share_sm = ShareObjectSM(share.status)
                new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
                share_sm.update_state(session, share, new_share_state)

                (
                    shared_tables,
                    shared_folders,
                    shared_buckets
                ) = ShareObjectRepository.get_share_data_items(session, share_uri, ShareItemStatus.Share_Approved.value)

                lock_acquired = cls.acquire_lock_with_retry(dataset.datasetUri, session, share.shareUri)

                if not lock_acquired:
                    log.error(f"Failed to acquire lock for dataset {dataset.datasetUri}. Exiting...")
                    for table in shared_tables:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session, share_uri, table.tableUri
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Share_Approved.value
                        )

                    for folder in shared_folders:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            folder.locationUri,
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Share_Approved.value
                        )

                    for bucket in shared_buckets:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            bucket.bucketUri,
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Share_Approved.value
                        )

                    share_object_SM = ShareObjectSM(share.status)
                    new_object_state = share_object_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
                    share_object_SM.update_state(session, share, new_object_state)
                    return False

            log.info(f'Granting permissions to folders: {shared_folders}')

            approved_folders_succeed = ProcessS3AccessPointShare.process_approved_shares(
                session,
                dataset,
                share,
                shared_folders,
                source_environment,
                target_environment,
                source_env_group,
                env_group
            )
            log.info(f'sharing folders succeeded = {approved_folders_succeed}')

            log.info('Granting permissions to S3 buckets')

            approved_s3_buckets_succeed = ProcessS3BucketShare.process_approved_shares(
                session,
                dataset,
                share,
                shared_buckets,
                source_environment,
                target_environment,
                source_env_group,
                env_group
            )
            log.info(f'sharing s3 buckets succeeded = {approved_s3_buckets_succeed}')

            log.info(f'Granting permissions to tables: {shared_tables}')
            approved_tables_succeed = ProcessLakeFormationShare(
                session,
                dataset,
                share,
                shared_tables,
                source_environment,
                target_environment,
                env_group,
            ).process_approved_shares()
            log.info(f'sharing tables succeeded = {approved_tables_succeed}')

            new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
            share_sm.update_state(session, share, new_share_state)

            return approved_folders_succeed and approved_s3_buckets_succeed and approved_tables_succeed

        except Exception as e:
            log.error(f"Error occurred during share approval: {e}")
            return False

        finally:
            lock_released = cls.release_lock(dataset.datasetUri, session, share.shareUri)
            if not lock_released:
                log.error(f"Failed to release lock for dataset {dataset.datasetUri}.")

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str):
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Revoke_Approved state
        3) Calls sharing folders processor to revoke share
        4) Checks if remaining folders are shared and effectuates clean up with folders processor
        5) Calls sharing tables processor for same or cross account sharing to revoke share
        6) Checks if remaining tables are shared and effectuates clean up with tables processor
        7) Calls sharing buckets processor to revoke share
        8) Updates share object State Machine with the Action: Finish

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if revoke succeeds
        False if folder or table revoking failed
        """
        try:
            with engine.scoped_session() as session:
                (
                    source_env_group,
                    env_group,
                    dataset,
                    share,
                    source_environment,
                    target_environment,
                ) = ShareObjectRepository.get_share_data(session, share_uri)

                share_sm = ShareObjectSM(share.status)
                new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
                share_sm.update_state(session, share, new_share_state)

                revoked_item_sm = ShareItemSM(ShareItemStatus.Revoke_Approved.value)

                (
                    revoked_tables,
                    revoked_folders,
                    revoked_buckets
                ) = ShareObjectRepository.get_share_data_items(session, share_uri, ShareItemStatus.Revoke_Approved.value)

                lock_acquired = cls.acquire_lock_with_retry(dataset.datasetUri, session, share.shareUri)

                if not lock_acquired:
                    log.error(f"Failed to acquire lock for dataset {dataset.datasetUri}. Exiting...")
                    for table in revoked_tables:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session, share_uri, table.tableUri
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Revoke_Approved.value
                        )

                    for folder in revoked_folders:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            folder.locationUri,
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Revoke_Approved.value
                        )

                    for bucket in revoked_buckets:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            bucket.bucketUri,
                        )
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Revoke_Approved.value
                        )

                    share_object_SM = ShareObjectSM(share.status)
                    new_object_state = share_object_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
                    share_object_SM.update_state(session, share, new_object_state)
                    return False

                new_state = revoked_item_sm.run_transition(ShareObjectActions.Start.value)
                revoked_item_sm.update_state(session, share_uri, new_state)

                log.info(f'Revoking permissions to folders: {revoked_folders}')

                revoked_folders_succeed = ProcessS3AccessPointShare.process_revoked_shares(
                    session,
                    dataset,
                    share,
                    revoked_folders,
                    source_environment,
                    target_environment,
                    source_env_group,
                    env_group,
                )
                log.info(f'revoking folders succeeded = {revoked_folders_succeed}')
                existing_shared_folders = ShareObjectRepository.check_existing_shared_items_of_type(
                    session,
                    share_uri,
                    ShareableType.StorageLocation.value
                )
                existing_shared_buckets = ShareObjectRepository.check_existing_shared_items_of_type(
                    session,
                    share_uri,
                    ShareableType.S3Bucket.value
                )
                existing_shared_items = existing_shared_folders or existing_shared_buckets
                log.info(f'Still remaining S3 resources shared = {existing_shared_items}')
                if not existing_shared_folders and revoked_folders:
                    log.info("Clean up S3 access points...")
                    clean_up_folders = ProcessS3AccessPointShare.clean_up_share(
                        session,
                        dataset=dataset,
                        share=share,
                        folder=revoked_folders[0],
                        source_environment=source_environment,
                        target_environment=target_environment,
                        source_env_group=source_env_group,
                        env_group=env_group
                    )
                    log.info(f"Clean up S3 successful = {clean_up_folders}")

                log.info('Revoking permissions to S3 buckets')

                revoked_s3_buckets_succeed = ProcessS3BucketShare.process_revoked_shares(
                    session,
                    dataset,
                    share,
                    revoked_buckets,
                    source_environment,
                    target_environment,
                    source_env_group,
                    env_group
                )
                log.info(f'revoking s3 buckets succeeded = {revoked_s3_buckets_succeed}')

                log.info(f'Revoking permissions to tables: {revoked_tables}')
                revoked_tables_succeed = ProcessLakeFormationShare(
                    session,
                    dataset,
                    share,
                    revoked_tables,
                    source_environment,
                    target_environment,
                    env_group,
                ).process_revoked_shares()
                log.info(f'revoking tables succeeded = {revoked_tables_succeed}')

                existing_pending_items = ShareObjectRepository.check_pending_share_items(session, share_uri)
                if existing_pending_items:
                    new_share_state = share_sm.run_transition(ShareObjectActions.FinishPending.value)
                else:
                    new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share, new_share_state)

                return revoked_folders_succeed and revoked_s3_buckets_succeed and revoked_tables_succeed

        except Exception as e:
            log.error(f"Error occurred during share revoking: {e}")
            return False

        finally:
            lock_released = cls.release_lock(dataset.datasetUri, session, share.shareUri)
            if not lock_released:
                log.error(f"Failed to release lock for dataset {dataset.datasetUri}.")

    @staticmethod
    def acquire_lock(dataset_uri, session, share_uri):
        """
        Attempts to acquire a lock on the dataset identified by dataset_id.

        Args:
            dataset_uri: The ID of the dataset for which the lock is being acquired.
            session (sqlalchemy.orm.Session): The SQLAlchemy session object used for interacting with the database.
            share_uri: The ID of the share that is attempting to acquire the lock.

        Returns:
            bool: True if the lock is successfully acquired, False otherwise.
        """
        try:
            # Execute the query to get the DatasetLock object
            dataset_lock = (
                session.query(DatasetLock)
                .filter(
                    and_(
                        DatasetLock.datasetUri == dataset_uri,
                        ~DatasetLock.isLocked
                    )
                )
                .with_for_update().first()
            )

            # Check if dataset_lock is not None before attempting to update
            if dataset_lock:
                # Update the attributes of the DatasetLock object
                dataset_lock.isLocked = True
                dataset_lock.acquiredBy = share_uri

                session.commit()
                return True
            else:
                log.info("DatasetLock not found for the given criteria.")
                return False
        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error("Error occurred while acquiring lock:", e)
            return False

    @staticmethod
    def acquire_lock_with_retry(dataset_uri, session, share_uri):
        for attempt in range(MAX_RETRIES):
            try:
                log.info(f"Attempting to acquire lock for dataset {dataset_uri} by share {share_uri}...")
                lock_acquired = DataSharingService.acquire_lock(dataset_uri, session, share_uri)
                if lock_acquired:
                    return True

                log.info(
                    f"Lock for dataset {dataset_uri} already acquired. Retrying in {RETRY_INTERVAL} seconds...")
                sleep(RETRY_INTERVAL)

            except Exception as e:
                log.error("Error occurred while retrying acquiring lock:", e)
                return False

        log.info(f"Max retries reached. Failed to acquire lock for dataset {dataset_uri}")
        return False

    @staticmethod
    def release_lock(dataset_uri, session, share_uri):
        """
        Releases the lock on the dataset identified by dataset_uri.

        Args:
            dataset_uri: The ID of the dataset for which the lock is being released.
            session (sqlalchemy.orm.Session): The SQLAlchemy session object used for interacting with the database.
            share_uri: The ID of the share that is attempting to release the lock.

        Returns:
            bool: True if the lock is successfully released, False otherwise.
        """
        try:
            log.info(f"Releasing lock for dataset: {dataset_uri} last acquired by share: {share_uri}")
            dataset_lock = (
                session.query(DatasetLock)
                .filter(
                    and_(
                        DatasetLock.datasetUri == dataset_uri,
                        DatasetLock.isLocked == True,
                        DatasetLock.acquiredBy == share_uri
                    )
                )
                .with_for_update().first()
            )

            if dataset_lock:
                dataset_lock.isLocked = False
                dataset_lock.acquiredBy = ''

                session.commit()
                return True
            else:
                log.info("DatasetLock not found for the given criteria.")
                return False

        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error("Error occurred while releasing lock:", e)
            return False

    @staticmethod
    def handle_share_items_failure_during_locking(session, share_item, share_item_status):
        """
        If lock is not acquired successfully, mark the share items as failed.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session object used for interacting with the database.
            share_item: The share item that needs to be marked failed during share.

        Returns:
            None
        """
        share_item_SM = ShareItemSM(share_item_status)
        new_state = share_item_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
        share_item_SM.update_state_single_item(session, share_item, new_state)

    @classmethod
    def verify_share(cls, engine: Engine, share_uri: str, status=None, healthStatus=ShareItemHealthStatus.PendingVerify.value):
        """
        2) Retrieves share data and items in specified status and health state (by default - PendingVerify)
        3) Calls verify folders processor to verify share and update health status
        4) Calls verify buckets processor to verify share and update health status
        5) Calls verify tables processor for same or cross account sharing to verify share and update health status

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        """
        with engine.scoped_session() as session:
            (
                source_env_group,
                env_group,
                dataset,
                share,
                source_environment,
                target_environment,
            ) = ShareObjectRepository.get_share_data(session, share_uri)

            (tables_to_verify, folders_to_verify, buckets_to_verify) = ShareObjectRepository.get_share_data_items(
                session, share_uri, status=status, healthStatus=healthStatus
            )

        log.info(f"Verifying permissions to folders: {folders_to_verify}")
        ProcessS3AccessPointShare.verify_shares(
            session,
            dataset,
            share,
            folders_to_verify,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

        log.info(f"Verifying permissions to S3 buckets: {buckets_to_verify}")
        ProcessS3BucketShare.verify_shares(
            session,
            dataset,
            share,
            buckets_to_verify,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

        log.info(f"Verifying permissions to tables: {tables_to_verify}")
        ProcessLakeFormationShare(
            session,
            dataset,
            share,
            tables_to_verify,
            source_environment,
            target_environment,
            env_group,
        ).verify_shares()
        return

    @classmethod
    def reapply_share(cls, engine: Engine, share_uri: str):
        """
        1) Retrieves share data and items in PendingReApply health state
        2) Calls sharing folders processor to re-apply share + update share item(s) health status
        3) Calls sharing buckets processor to re-apply share + update share item(s) health status
        4) Calls sharing tables processor for same or cross account sharing to re-apply share + update share item(s) health status

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if re-apply of share item(s) succeeds,
        False if any re-apply of share item(s) failed
        """
        try:
            with engine.scoped_session() as session:
                (
                    source_env_group,
                    env_group,
                    dataset,
                    share,
                    source_environment,
                    target_environment,
                ) = ShareObjectRepository.get_share_data(session, share_uri)

                (reapply_tables, reapply_folders, reapply_buckets) = ShareObjectRepository.get_share_data_items(
                    session, share_uri, None, ShareItemHealthStatus.PendingReApply.value
                )

                lock_acquired = cls.acquire_lock_with_retry(dataset.datasetUri, session, share.shareUri)
                if not lock_acquired:
                    log.error(f"Failed to acquire lock for dataset {dataset.datasetUri}. Exiting...")
                    error_message = f"SHARING PROCESS TIMEOUT: Failed to acquire lock for dataset {dataset.datasetUri}"
                    for table in reapply_tables:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session, share_uri, table.tableUri
                        )
                        ShareObjectRepository.update_share_item_health_status(
                            session, share_item, ShareItemHealthStatus.Unhealthy.value, error_message, datetime.now()
                        )

                    for folder in reapply_folders:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            folder.locationUri,
                        )
                        ShareObjectRepository.update_share_item_health_status(
                            session, share_item, ShareItemHealthStatus.Unhealthy.value, error_message, datetime.now()
                        )

                    for bucket in reapply_buckets:
                        share_item = ShareObjectRepository.find_sharable_item(
                            session,
                            share_uri,
                            bucket.bucketUri,
                        )
                        ShareObjectRepository.update_share_item_health_status(
                            session, share_item, ShareItemHealthStatus.Unhealthy.value, error_message, datetime.now()
                        )
                    return False

            log.info(f"Reapply permissions to folders: {reapply_folders}")
            reapply_folders_succeed = ProcessS3AccessPointShare.process_approved_shares(
                session,
                dataset,
                share,
                reapply_folders,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
                True,
            )
            log.info(f"reapply folders succeeded = {reapply_folders_succeed}")

            log.info("Reapply permissions to S3 buckets")
            reapply_s3_buckets_succeed = ProcessS3BucketShare.process_approved_shares(
                session,
                dataset,
                share,
                reapply_buckets,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
                True,
            )
            log.info(f"Reapply s3 buckets succeeded = {reapply_s3_buckets_succeed}")

            log.info(f"Reapply permissions to tables: {reapply_tables}")
            reapply_tables_succeed = ProcessLakeFormationShare(
                session, dataset, share, reapply_tables, source_environment, target_environment, env_group, True
            ).process_approved_shares()
            log.info(f"Reapply tables succeeded = {reapply_tables_succeed}")

            return reapply_folders_succeed and reapply_s3_buckets_succeed and reapply_tables_succeed
        except Exception as e:
            log.error(f"Error occurred during share approval: {e}")
            return False

        finally:
            lock_released = cls.release_lock(dataset.datasetUri, session, share.shareUri)
            if not lock_released:
                log.error(f"Failed to release lock for dataset {dataset.datasetUri}.")
