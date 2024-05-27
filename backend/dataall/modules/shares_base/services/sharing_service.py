import logging
from datetime import datetime
from typing import List, Any, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
from sqlalchemy import and_
from time import sleep
from dataall.base.db import Engine
from dataall.base.aws.iam import IAM
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.shares_enums import ShareItemHealthStatus, ShareObjectActions, ShareItemStatus
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetLock

log = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_INTERVAL = 60


@dataclass
class ShareData:
    share: ShareObject
    dataset: Any
    source_environment: Environment
    target_environment: Environment
    source_env_group: EnvironmentGroup
    env_group: EnvironmentGroup


class SharesProcessorInterface(ABC):
    @abstractmethod
    def process_approved_shares(self) -> bool:
        """Executes a series of actions to share items using the share manager. Returns True if the sharing was successful"""
        ...

    @abstractmethod
    def process_revoked_shares(self) -> bool:
        """Executes a series of actions to revoke share items using the share manager. Returns True if the revoking was successful"""
        ...

    @abstractmethod
    def verify_shares(self) -> bool:
        """Executes a series of actions to verify share items using the share manager. Returns True if the verifying was successful"""
        ...


@dataclass
class SharingProcessorDefinition:
    name: str
    Processor: Any
    shareable_type: Any
    shareable_uri: Any


class SharingService:  # Replaces DataSharingService, Still unused I just left it to explain the usage of the SharesProcessorInterface
    _SHARING_PROCESSORS: Dict[str, SharingProcessorDefinition] = {}

    @classmethod
    def register_processor(cls, processor: SharingProcessorDefinition) -> None:
        cls._SHARING_PROCESSORS[processor.name] = processor

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Calls corresponding SharesInterface.process_approved_shares for available items
        4) Updates share object State Machine with the Action: Finish

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if sharing succeeds,
        False if sharing fails
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls.get_share_data_and_items(
                session, share_uri, ShareItemStatus.Share_Approved.value
            )
            try:
                share_sm = ShareObjectSM(share_data.share.status)
                new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
                share_sm.update_state(session, share_data.share, new_share_state)

                log.info(f'Verifying principal IAM Role {share_data.share.principalIAMRoleName}')
                share_successful = cls.verify_principal_role(session, share_data.share)
                # If principal role doesn't exist, all share items are unhealthy, no use of further checks
                if share_successful:
                    lock_acquired = cls.acquire_lock_with_retry(
                        share_data.dataset.datasetUri, session, share_data.share.shareUri
                    )
                    if not lock_acquired:
                        log.error(f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}. Exiting...')
                        for share_item in share_items:
                            cls.handle_share_items_failure_during_locking(
                                session, share_item, ShareItemStatus.Share_Approved.value
                            )
                        share_object_SM = ShareObjectSM(share_data.share.status)
                        new_object_state = share_object_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
                        share_object_SM.update_state(session, share_data.share, new_object_state)
                        return False
                    for type, processor in cls._SHARING_PROCESSORS.items():
                        log.info(f'Granting permissions of {type}')
                        shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                            session,
                            share_data.share,
                            processor.shareable_type,
                            processor.shareable_uri,
                            status=ShareItemStatus.Share_Approved.value,
                        )
                        success = processor.Processor(session, share_data, shareable_items).process_approved_shares()
                        log.info(f'Sharing {type} succeeded = {success}')
                        if not success:
                            share_successful = False
                else:
                    log.info(f'Principal IAM Role {share_data.share.principalIAMRoleName} does not exist')
                    for share_item in share_items:
                        ShareObjectRepository.update_share_item_status(
                            session,
                            share_item.shareItemUri,
                            ShareItemStatus.Share_Failed.value,
                        )

                new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share_data.share, new_share_state)

                return share_successful

            except Exception as e:
                log.error(f'Error occurred during share approval: {e}')
                return False

            finally:
                lock_released = cls.release_lock(share_data.dataset.datasetUri, session, share_data.share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {share_data.dataset.datasetUri}.')

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Revoke_Approved state
        3) Calls corresponding SharesInterface.process_revoke_shares for available items
        4) Updates share object State Machine with the Action: Finish

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
                share_data, share_items = cls.get_share_data_and_items(
                    session, share_uri, ShareItemStatus.Revoke_Approved.value
                )

                share_sm = ShareObjectSM(share_data.share.status)
                new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
                share_sm.update_state(session, share_data.share, new_share_state)

                revoked_item_sm = ShareItemSM(ShareItemStatus.Revoke_Approved.value)

                lock_acquired = cls.acquire_lock_with_retry(
                    share_data.dataset.datasetUri, session, share_data.share.shareUri
                )
                revoke_successful = True
                if not lock_acquired:
                    log.error(f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}. Exiting...')
                    for share_item in share_items:
                        cls.handle_share_items_failure_during_locking(
                            session, share_item, ShareItemStatus.Revoke_Approved.value
                        )

                    share_object_SM = ShareObjectSM(share_data.share.status)
                    new_object_state = share_object_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
                    share_object_SM.update_state(session, share_data.share, new_object_state)
                    return False

                new_state = revoked_item_sm.run_transition(ShareObjectActions.Start.value)
                revoked_item_sm.update_state(session, share_uri, new_state)

                for type, processor in cls._SHARING_PROCESSORS.items():
                    shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                        session,
                        share_data.share,
                        processor.shareable_type,
                        processor.shareable_uri,
                        status=ShareItemStatus.Revoke_Approved.value,
                    )
                    log.info(f'Revoking permissions with {type}')
                    success = processor.Processor(session, share_data, shareable_items).process_revoked_shares()
                    log.info(f'Revoking {type} succeeded = {success}')
                    if not success:
                        revoke_successful = False

                existing_pending_items = ShareObjectRepository.check_pending_share_items(session, share_uri)
                if existing_pending_items:
                    new_share_state = share_sm.run_transition(ShareObjectActions.FinishPending.value)
                else:
                    new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share_data.share, new_share_state)

                return revoke_successful
        except Exception as e:
            log.error(f'Error occurred during share revoking: {e}')
            return False

        finally:
            with engine.scoped_session() as session:
                lock_released = cls.release_lock(share_data.dataset.datasetUri, session, share_data.share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {share_data.dataset.datasetUri}.')

    @classmethod
    def verify_share(cls, engine: Engine, share_uri: str, status: str, healthStatus) -> bool:
        """
        1) Retrieves share data and items in specified status and health state (by default - PendingVerify)
        2) Calls corresponding SharesInterface.verify_shares

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls.get_share_data_and_items(session, share_uri, status, healthStatus)

            log.info(f'Verifying principal IAM Role {share_data.share.principalIAMRoleName}')
            # If principal role doesn't exist, all share items are unhealthy, no use of further checks
            if not cls.verify_principal_role(session, share_data.share):
                ShareObjectRepository.update_all_share_items_status(
                    session,
                    share_uri,
                    previous_health_status=healthStatus,
                    new_health_status=ShareItemHealthStatus.Unhealthy.value,
                    message=f'Share principal Role {share_data.share.principalIAMRoleName} is not found.',
                )
                return True

            for type, processor in cls._SHARING_PROCESSORS.items():
                shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                    session,
                    share_data.share,
                    processor.shareable_type,
                    processor.shareable_uri,
                    status=status,
                    healthStatus=healthStatus,
                )
                log.info(f'Verifying permissions with {type}')
                processor.Processor(session, share_data, shareable_items).verify_shares()

        return True

    @classmethod
    def reapply_share(cls, engine: Engine, share_uri: str) -> bool:
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
                share_data, share_items = cls.get_share_data_and_items(
                    session, share_uri, None, ShareItemHealthStatus.PendingReApply.value
                )

                log.info(f'Verifying principal IAM Role {share_data.share.principalIAMRoleName}')
                # If principal role doesn't exist, all share items are unhealthy, no use of further checks
                if not cls.verify_principal_role(session, share_data.share):
                    return False

                reapply_successful = True
                lock_acquired = cls.acquire_lock_with_retry(
                    share_data.dataset.datasetUri, session, share_data.share.shareUri
                )
                if not lock_acquired:
                    log.error(f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}. Exiting...')
                    error_message = (
                        f'SHARING PROCESS TIMEOUT: Failed to acquire lock for dataset {share_data.dataset.datasetUri}'
                    )
                    for share_item in share_items:
                        ShareObjectRepository.update_share_item_health_status(
                            session, share_item, ShareItemHealthStatus.Unhealthy.value, error_message, datetime.now()
                        )
                    return False

            for type, processor in cls._SHARING_PROCESSORS.items():
                log.info(f'Reapplying permissions to {type}')
                shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                    session,
                    share_data.share,
                    processor.shareable_type,
                    processor.shareable_uri,
                    None,
                    ShareItemHealthStatus.PendingReApply.value,
                )
                log.info(f'Reapplying permissions with {type}')
                success = processor.Processor(session, share_data, shareable_items).proccess_approved_shares()
                log.info(f'Reapplying {type} succeeded = {success}')
                if not success:
                    reapply_successful = False

            return reapply_successful
        except Exception as e:
            log.error(f'Error occurred during share approval: {e}')
            return False

        finally:
            with engine.scoped_session() as session:
                lock_released = cls.release_lock(share_data.dataset.datasetUri, session, share_data.share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {share_data.dataset.datasetUri}.')

    @staticmethod
    def get_share_data_and_items(session, share_uri, status, healthStatus=None):
        data = ShareObjectRepository.get_share_data(session, share_uri)
        share_data = ShareData(
            share=data[0],
            dataset=data[1],
            source_environment=data[2],
            target_environment=data[3],
            source_env_group=data[4],
            env_group=data[5],
        )
        share_items = ShareObjectRepository.get_all_share_items_in_share(
            session=session, share_uri=share_uri, status=status, healthStatus=healthStatus
        )
        return share_data, share_items

    @staticmethod
    def verify_principal_role(session, share: ShareObject) -> bool:
        role_name = share.principalIAMRoleName
        env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        principal_role = IAM.get_role_arn_by_name(account_id=env.AwsAccountId, region=env.region, role_name=role_name)
        return principal_role is not None

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
                .filter(and_(DatasetLock.datasetUri == dataset_uri, ~DatasetLock.isLocked))
                .with_for_update()
                .first()
            )

            # Check if dataset_lock is not None before attempting to update
            if dataset_lock:
                # Update the attributes of the DatasetLock object
                dataset_lock.isLocked = True
                dataset_lock.acquiredBy = share_uri

                session.commit()
                return True
            else:
                log.info('DatasetLock not found for the given criteria.')
                return False
        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error('Error occurred while acquiring lock:', e)
            return False

    @staticmethod
    def acquire_lock_with_retry(dataset_uri, session, share_uri):
        for attempt in range(MAX_RETRIES):
            try:
                log.info(f'Attempting to acquire lock for dataset {dataset_uri} by share {share_uri}...')
                lock_acquired = SharingService.acquire_lock(dataset_uri, session, share_uri)
                if lock_acquired:
                    return True

                log.info(f'Lock for dataset {dataset_uri} already acquired. Retrying in {RETRY_INTERVAL} seconds...')
                sleep(RETRY_INTERVAL)

            except Exception as e:
                log.error('Error occurred while retrying acquiring lock:', e)
                return False

        log.info(f'Max retries reached. Failed to acquire lock for dataset {dataset_uri}')
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
            log.info(f'Releasing lock for dataset: {dataset_uri} last acquired by share: {share_uri}')
            dataset_lock = (
                session.query(DatasetLock)
                .filter(
                    and_(
                        DatasetLock.datasetUri == dataset_uri,
                        DatasetLock.isLocked == True,
                        DatasetLock.acquiredBy == share_uri,
                    )
                )
                .with_for_update()
                .first()
            )

            if dataset_lock:
                dataset_lock.isLocked = False
                dataset_lock.acquiredBy = ''

                session.commit()
                return True
            else:
                log.info('DatasetLock not found for the given criteria.')
                return False

        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error('Error occurred while releasing lock:', e)
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
