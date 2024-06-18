import logging
from typing import Any, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
from sqlalchemy import and_, func
from time import sleep
from dataall.base.db import Engine, get_engine
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareObjectActions,
    ShareItemActions,
    ShareItemStatus,
    ShareableType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.dataset_sharing.services.share_notification_service import ShareNotificationService
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.notifications.db.notification_models import Notification
from dataall.modules.shares_base.services.share_object_service import (
    ShareObjectService,
)
from dataall.modules.shares_base.services.share_exceptions import (
    PrincipalRoleNotFound,
    DatasetLockTimeout,
)
from dataall.modules.datasets_base.db.dataset_models import DatasetLock

log = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_INTERVAL = 60


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
    type: ShareableType
    Processor: Any
    shareable_type: Any
    shareable_uri: Any


@dataclass
class ShareData:
    share: ShareObject
    dataset: Any
    source_environment: Environment
    target_environment: Environment
    source_env_group: EnvironmentGroup
    env_group: EnvironmentGroup


class SharingService:
    _SHARING_PROCESSORS: Dict[ShareableType, SharingProcessorDefinition] = {}

    @classmethod
    def register_processor(cls, processor: SharingProcessorDefinition) -> None:
        cls._SHARING_PROCESSORS[processor.type] = processor

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Verifies principal IAM Role
        4) Acquires dataset lock and locks dataset while sharing
        5) Calls corresponding SharesInterface.process_approved_shares for available items
        6) [Finally] Updates share object State Machine with the Action: Finish and releases dataset lock

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
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, ShareItemStatus.Share_Approved.value
            )
            share_object_sm = ShareObjectSM(share_data.share.status)
            share_item_sm = ShareItemSM(ShareItemStatus.Share_Approved.value)

            log.info(f'Starting share {share_data.share.shareUri}')
            new_share_state = share_object_sm.run_transition(ShareObjectActions.Start.value)
            share_object_sm.update_state(session, share_data.share, new_share_state)
            share_successful = True
            try:
                if not ShareObjectService.verify_principal_role(session, share_data.share):
                    raise PrincipalRoleNotFound(
                        'process approved shares',
                        f'Principal role {share_data.share.principalIAMRoleName} is not found.',
                    )
                if not cls.acquire_lock_with_retry(share_data.dataset.datasetUri, session, share_data.share.shareUri):
                    raise DatasetLockTimeout(
                        'process approved shares',
                        f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}',
                    )
                for type, processor in cls._SHARING_PROCESSORS.items():
                    try:
                        log.info(f'Granting permissions of {type.value}')
                        shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                            session,
                            share_data.share,
                            processor.shareable_type,
                            processor.shareable_uri,
                            status=ShareItemStatus.Share_Approved.value,
                        )
                        success = processor.Processor(session, share_data, shareable_items).process_approved_shares()
                        log.info(f'Sharing {type.value} succeeded = {success}')
                        if not success:
                            share_successful = False
                    except Exception as e:
                        log.error(f'Error occurred during sharing of {type.value}: {e}')
                        ShareObjectRepository.update_share_item_status_batch(
                            session,
                            share_uri,
                            old_status=ShareItemStatus.Share_Approved.value,
                            new_status=ShareItemStatus.Share_Failed.value,
                            share_item_type=processor.type.value,
                        )
                        ShareObjectRepository.update_share_item_status_batch(
                            session,
                            share_uri,
                            old_status=ShareItemStatus.Share_In_Progress.value,
                            new_status=ShareItemStatus.Share_Failed.value,
                            share_item_type=processor.type.value,
                        )
                        share_successful = False
                return share_successful

            except Exception as e:
                log.error(f'Error occurred during share approval: {e}')
                new_share_item_state = share_item_sm.run_transition(ShareItemActions.Failure.value)
                share_item_sm.update_state(session, share_data.share.shareUri, new_share_item_state)
                return False

            finally:
                new_share_state = share_object_sm.run_transition(ShareObjectActions.Finish.value)
                share_object_sm.update_state(session, share_data.share, new_share_state)
                lock_released = cls.release_lock(share_data.dataset.datasetUri, session, share_data.share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {share_data.dataset.datasetUri}.')

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Revoke_Approved state
        3) Acquires dataset lock and locks dataset while revoking
        4) Calls corresponding SharesInterface.process_revoke_shares for available items
        5) [Finally] Updates share object State Machine with the Action: Finish or FinishPending and releases dataset lock

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if revoking succeeds
        False if revoking failed
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, ShareItemStatus.Revoke_Approved.value
            )

            share_sm = ShareObjectSM(share_data.share.status)
            share_item_sm = ShareItemSM(ShareItemStatus.Revoke_Approved.value)

            log.info(f'Starting revoke {share_data.share.shareUri}')
            new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
            share_sm.update_state(session, share_data.share, new_share_state)
            revoke_successful = True
            try:
                if not ShareObjectService.verify_principal_role(session, share_data.share):
                    raise PrincipalRoleNotFound(
                        'process revoked shares',
                        f'Principal role {share_data.share.principalIAMRoleName} is not found.',
                    )
                if not cls.acquire_lock_with_retry(share_data.dataset.datasetUri, session, share_data.share.shareUri):
                    raise DatasetLockTimeout(
                        'process revoked shares',
                        f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}',
                    )

                for type, processor in cls._SHARING_PROCESSORS.items():
                    try:
                        shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                            session,
                            share_data.share,
                            processor.shareable_type,
                            processor.shareable_uri,
                            status=ShareItemStatus.Revoke_Approved.value,
                        )
                        log.info(f'Revoking permissions with {type.value}')
                        success = processor.Processor(session, share_data, shareable_items).process_revoked_shares()
                        log.info(f'Revoking {type.value} succeeded = {success}')
                        if not success:
                            revoke_successful = False
                    except Exception as e:
                        log.error(f'Error occurred during share revoking of {type.value}: {e}')
                        ShareObjectRepository.update_share_item_status_batch(
                            session,
                            share_uri,
                            old_status=ShareItemStatus.Revoke_Approved.value,
                            new_status=ShareItemStatus.Revoke_Failed.value,
                            share_item_type=processor.type.value,
                        )
                        ShareObjectRepository.update_share_item_status_batch(
                            session,
                            share_uri,
                            old_status=ShareItemStatus.Revoke_In_Progress.value,
                            new_status=ShareItemStatus.Revoke_Failed.value,
                            share_item_type=processor.type.value,
                        )
                        revoke_successful = False

                return revoke_successful
            except Exception as e:
                log.error(f'Error occurred during share revoking: {e}')
                new_share_item_state = share_item_sm.run_transition(ShareItemActions.Failure.value)
                share_item_sm.update_state(session, share_data.share.shareUri, new_share_item_state)
                return False

            finally:
                existing_pending_items = ShareObjectRepository.check_pending_share_items(session, share_uri)
                if existing_pending_items:
                    new_share_state = share_sm.run_transition(ShareObjectActions.FinishPending.value)
                else:
                    new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share_data.share, new_share_state)

                lock_released = cls.release_lock(share_data.dataset.datasetUri, session, share_data.share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {share_data.dataset.datasetUri}.')

    @classmethod
    def verify_share(
        cls,
        engine: Engine,
        share_uri: str,
        status: str = None,
        healthStatus: str = ShareItemHealthStatus.PendingVerify.value,
    ) -> bool:
        """
        1) Retrieves share data and items in specified status and health state (by default - PendingVerify)
        2) Calls corresponding SharesInterface.verify_shares

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns True when completed
        -------
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(session, share_uri, status, healthStatus)

            log.info(f'Verifying principal IAM Role {share_data.share.principalIAMRoleName}')
            if not ShareObjectService.verify_principal_role(session, share_data.share):
                log.error(
                    f'Failed to get Principal IAM Role {share_data.share.principalIAMRoleName}, updating health status...'
                )
                ShareObjectRepository.update_share_item_health_status_batch(
                    session,
                    share_uri,
                    old_status=healthStatus,
                    new_status=ShareItemHealthStatus.Unhealthy.value,
                    message=f'Share principal Role {share_data.share.principalIAMRoleName} not found. Check the team or consumption IAM role used.',
                )
                return True

            for type, processor in cls._SHARING_PROCESSORS.items():
                try:
                    shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                        session,
                        share_data.share,
                        processor.shareable_type,
                        processor.shareable_uri,
                        status=status,
                        healthStatus=healthStatus,
                    )
                    log.info(f'Verifying permissions with {type.value}')
                    processor.Processor(session, share_data, shareable_items).verify_shares()
                except Exception as e:
                    log.error(f'Error occurred during share verifying of {type.value}: {e}')

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
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, None, ShareItemHealthStatus.PendingReApply.value
            )
            try:
                log.info(f'Verifying principal IAM Role {share_data.share.principalIAMRoleName}')
                reapply_successful = ShareObjectService.verify_principal_role(session, share_data.share)
                if not reapply_successful:
                    log.error(f'Failed to get Principal IAM Role {share_data.share.principalIAMRoleName}, exiting...')
                    return False
                else:
                    lock_acquired = cls.acquire_lock_with_retry(
                        share_data.dataset.datasetUri, session, share_data.share.shareUri
                    )
                    if not lock_acquired:
                        log.error(f'Failed to acquire lock for dataset {share_data.dataset.datasetUri}, exiting...')
                        error_message = f'SHARING PROCESS TIMEOUT: Failed to acquire lock for dataset {share_data.dataset.datasetUri}'
                        ShareObjectRepository.update_share_item_health_status_batch(
                            session,
                            share_uri,
                            old_status=ShareItemHealthStatus.PendingReApply.value,
                            new_status=ShareItemHealthStatus.Unhealthy.value,
                            message=error_message,
                        )
                        return False

                    for type, processor in cls._SHARING_PROCESSORS.items():
                        try:
                            log.info(f'Reapplying permissions to {type.value}')
                            shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                                session,
                                share_data.share,
                                processor.shareable_type,
                                processor.shareable_uri,
                                None,
                                ShareItemHealthStatus.PendingReApply.value,
                            )
                            success = processor.Processor(
                                session, share_data, shareable_items
                            ).process_approved_shares()
                            log.info(f'Reapplying {type.value} succeeded = {success}')
                            if not success:
                                reapply_successful = False
                        except Exception as e:
                            log.error(f'Error occurred during share reapplying of {type.value}: {e}')

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
    def fetch_pending_shares(engine):
        """
        A method used by the scheduled ECS Task to run fetch_pending_shares() process against ALL shared objects in ALL
        active share objects within dataall
        """
        with engine.scoped_session() as session:
            pending_shares = (
                session.query(ShareObject)
                .join(Notification, and_(
                    ShareObject.shareUri == func.split_part(Notification.target_uri, '|', 1),
                    ShareObject.datasetUri == func.split_part(Notification.target_uri, '|', 2),

                ))
                .filter(
                    and_(
                        Notification.type == 'SHARE_OBJECT_SUBMITTED',
                        ShareObject.status == 'Submitted'
                    )
                )
                .all()
            )
            return pending_shares

    @staticmethod
    def _get_share_data(session, uri):
        share = ShareObjectRepository.get_share_by_uri(session, uri)
        dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObjectRepository.get_share_items_states(session, uri)
        return share, dataset, share_items_states

    @classmethod
    def persistent_email_reminder(cls, uri: str, envname):
        """
        A method used by the scheduled ECS Task to send email notifications to the requestor of the share object
        """
        engine = get_engine(envname=envname)

        with engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            ShareNotificationService(
                session=session, dataset=dataset, share=share
            ).notify_persistent_email_reminder(email_id=share.owner, engine=engine)
            log.info(f'Email reminder sent for share {share.shareUri}')

    @staticmethod
    def _get_share_data_and_items(session, share_uri, status, healthStatus=None):
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
