import logging

from dataall.core.resource_lock.db.resource_lock_models import ResourceLock
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from time import sleep
from typing import List, Tuple
from contextlib import contextmanager
from dataall.base.db.exceptions import ResourceLockTimeout

log = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_INTERVAL = 60


class ResourceLockRepository:
    @staticmethod
    def _acquire_locks(resources, session, acquired_by_uri, acquired_by_type):
        """
        Attempts to acquire/create one or more locks on the resources identified by resourceUri and resourceType.

        Args:
            resources: List of resource tuples (resourceUri, resourceType) to acquire locks for.
            session (sqlalchemy.orm.Session): The SQLAlchemy session object used for interacting with the database.
            acquired_by_uri: The ID of the resource that is attempting to acquire the lock.
            acquired_by_type: The resource type that is attempting to acquire the lock.qu

        Returns:
            bool: True if the lock is successfully acquired, False otherwise.
        """
        try:
            # Execute the query to get the ResourceLock object
            filter_conditions = [
                and_(
                    ResourceLock.resourceUri == resource[0],
                    ResourceLock.resourceType == resource[1],
                )
                for resource in resources
            ]

            if not session.query(ResourceLock).filter(or_(*filter_conditions)).first():
                records = []
                for resource in resources:
                    records.append(
                        ResourceLock(
                            resourceUri=resource[0],
                            resourceType=resource[1],
                            acquiredByUri=acquired_by_uri,
                            acquiredByType=acquired_by_type,
                        )
                    )
                session.add_all(records)
                session.commit()
                return True
            else:
                log.info(
                    'Not all ResourceLocks were found. One or more ResourceLocks may be acquired by another resource...'
                )
                return False
        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error('Error occurred while acquiring lock:', e)
            return False

    @staticmethod
    def _release_lock(session, resource_uri, resource_type, share_uri):
        """
        Releases/delete the lock on the resource identified by resource_uri, resource_type.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session object used for interacting with the database.
            resource_uri: The ID of the resource that owns the lock.
            resource_type: The type of the resource that owns the lock.
            share_uri: The ID of the share that is attempting to release the lock.

        Returns:
            bool: True if the lock is successfully released, False otherwise.
        """
        try:
            log.info(f'Releasing lock for resource: {resource_uri=}, {resource_type=}')

            resource_lock = (
                session.query(ResourceLock)
                .filter(
                    and_(
                        ResourceLock.resourceUri == resource_uri,
                        ResourceLock.resourceType == resource_type,
                        ResourceLock.acquiredByUri == share_uri,
                    )
                )
                .with_for_update()
                .first()
            )

            if resource_lock:
                session.delete(resource_lock)
                session.commit()
                return True
            else:
                log.info(f'ResourceLock not found for resource: {resource_uri=}, {resource_type=}')
                return False

        except Exception as e:
            session.expunge_all()
            session.rollback()
            log.error('Error occurred while releasing lock:', e)
            return False

    @staticmethod
    @contextmanager
    def acquire_lock_with_retry(
        resources: List[Tuple[str, str]], session: Session, acquired_by_uri: str, acquired_by_type: str
    ):
        retries_remaining = MAX_RETRIES
        log.info(f'Attempting to acquire lock for resources {resources} by share {acquired_by_uri}...')
        while not (
            lock_acquired := ResourceLockRepository._acquire_locks(
                resources, session, acquired_by_uri, acquired_by_type
            )
        ):
            log.info(
                f'Lock for one or more resources {resources} already acquired. Retrying in {RETRY_INTERVAL} seconds...'
            )
            sleep(RETRY_INTERVAL)
            retries_remaining -= 1
            if retries_remaining <= 0:
                raise ResourceLockTimeout(
                    'process shares',
                    f'Failed to acquire lock for one or more of {resources=}',
                )
        try:
            yield lock_acquired
        finally:
            for resource in resources:
                ResourceLockRepository._release_lock(session, resource[0], resource[1], acquired_by_uri)
