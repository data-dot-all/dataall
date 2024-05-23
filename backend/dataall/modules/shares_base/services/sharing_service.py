import logging
from typing import List
from abc import ABC, abstractmethod
from sqlalchemy import and_
from time import sleep
from dataall.base.db import Engine
from dataall.base.aws.iam import IAM
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareObjectActions,
    ShareItemStatus,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetLock

log = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_INTERVAL = 60


class SharesManagerInterface(ABC):
    @abstractmethod
    def __init__(
        self,
        session,
        dataset,
        share,
        items,
        source_environment,
        target_environment,
        source_env_group,
        env_group,
        reapply,
    ):
        """Ensures that the manager used is initalized with the paramters passed"""
        ...


class SharesProcessorInterface(ABC):
    @staticmethod
    @abstractmethod
    def initialize_share_managers(
        session, dataset, share, items, source_environment, target_environment, source_env_group, env_group, reapply
    ) -> List[SharesManagerInterface]:
        """Initializes the specific technology share manager that encapsulates all API calls for sharing"""
        ...

    @staticmethod
    @abstractmethod
    def process_approved_shares(share_managers: List[SharesManagerInterface]) -> bool:
        """Executes a series of actions to share items using the share manager. Returns True if the sharing was successful"""
        ...

    @staticmethod
    @abstractmethod
    def process_revoked_shares(share_managers: List[SharesManagerInterface]) -> bool:
        """Executes a series of actions to revoke share items using the share manager. Returns True if the revoking was successful"""
        ...

    @staticmethod
    @abstractmethod
    def verify_shares(share_managers: List[SharesManagerInterface]) -> bool:
        """Executes a series of actions to verify share items using the share manager. Returns True if the verifying was successful"""
        ...


class SharingService:  # Replaces DataSharingService, Still unused I just left it to explain the usage of the SharesProcessorInterface
    _SHARING_SERVICES = {}

    def register_service(self, service_name: str, service: SharesProcessorInterface):
        SharingService._SHARING_SERVICES[service_name] = service

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Calls corresponding SharesInterface.share_items for available items
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

                shared_items_dict = ShareObjectRepository.get_share_data_items(
                    session, share_uri, ShareItemStatus.Share_Approved.value
                )

                log.info(f'Verifying principal IAM Role {share.principalIAMRoleName}')
                share_successful = cls.verify_principal_role(session, share)
                # If principal role doesn't exist, all share items are unhealthy, no use of further checks
                if share_successful:
                    lock_acquired = cls.acquire_lock_with_retry(dataset.datasetUri, session, share.shareUri)

                    if not lock_acquired:
                        log.error(f'Failed to acquire lock for dataset {dataset.datasetUri}. Exiting...')
                        for item in list(shared_items_dict.values()):
                            share_item = ShareObjectRepository.find_sharable_item(
                                session,
                                share_uri,
                                item.itemUri,  # TODO Need to verify if we can ue item.itemUri instead of table.tableUri
                            )

                            cls.handle_share_items_failure_during_locking(
                                session, share_item, ShareItemStatus.Share_Approved.value
                            )
                        share_object_SM = ShareObjectSM(share.status)
                        new_object_state = share_object_SM.run_transition(ShareObjectActions.AcquireLockFailure.value)
                        share_object_SM.update_state(session, share, new_object_state)
                        return False

                    for type, items in shared_items_dict.items():
                        log.info(f'Granting permissions to {type}: {items}')
                        reapply = False
                        share_manager = cls._SHARING_SERVICES[type].initialize_share_manager(
                            session,
                            dataset,
                            share,
                            items,
                            source_environment,
                            target_environment,
                            source_env_group,
                            env_group,
                        )
                        success = cls._SHARING_SERVICES[type].process_approved_shares(share_manager)
                        log.info(f'Sharing {type} succeeded = {success}')
                        if not success:
                            share_successful = False
                else:
                    log.info(f'Principal IAM Role {share.principalIAMRoleName} does not exist')
                    items = ShareObjectRepository.get_all_shareable_items(
                        session,
                        share_uri,
                        ShareItemStatus.Share_Approved.value,
                    )
                    for item in items:
                        ShareObjectRepository.update_share_item_status(
                            session,
                            item.shareItemUri,
                            ShareItemStatus.Share_Failed.value,
                        )

                new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share, new_share_state)

                log.info('Attaching TABLE/FOLDER READ permissions to successfully shared items...')
                # TODO: move to specific processor
                # ShareObjectService.attach_dataset_table_read_permission(session, share)
                # ShareObjectService.attach_dataset_folder_read_permission(session, share)

                return share_successful

        except Exception as e:
            log.error(f'Error occurred during share approval: {e}')
            return False

        finally:
            with engine.scoped_session() as session:
                lock_released = cls.release_lock(dataset.datasetUri, session, share.shareUri)
                if not lock_released:
                    log.error(f'Failed to release lock for dataset {dataset.datasetUri}.')

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str) -> bool:
        # TODO
        pass

    @classmethod
    def verify_share(cls, engine: Engine, share_uri: str, status: str, healthStatus) -> bool:
        # TODO
        pass

    @classmethod
    def reapply_share(cls, engine: Engine, share_uri: str) -> bool:
        # TODO
        pass

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
