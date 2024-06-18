import logging

from dataall.core.resource_lock.db.resource_lock_models import ResourceLock
from sqlalchemy import and_, or_

log = logging.getLogger(__name__)


class ResourceLockRepository:
    @staticmethod
    def create_resource_lock(
        session, resource_uri, resource_type, is_locked=False, acquired_by_uri=None, acquired_by_type=None
    ):
        resource_lock = ResourceLock(
            resourceUri=resource_uri,
            resourceType=resource_type,
            isLocked=is_locked,
            acquiredByUri=acquired_by_uri,
            acquiredByType=acquired_by_type,
        )
        session.add(resource_lock)
        session.commit()

    @staticmethod
    def delete_resource_lock(session, resource_uri):
        resource_lock = session.query(ResourceLock).filter(ResourceLock.resourceUri == resource_uri).first()
        session.delete(resource_lock)
        session.commit()

    @staticmethod
    def acquire_locks(resources, session, acquired_by_uri, acquired_by_type):
        """
        Attempts to acquire one or more locks on the resources identified by resourceUri and resourceType.

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
                    ~ResourceLock.isLocked,
                )
                for resource in resources
            ]
            resource_locks = session.query(ResourceLock).filter(or_(*filter_conditions)).with_for_update().all()

            # Ensure lock record found for each resource
            if len(resource_locks) == len(resources):
                # Update the attributes of the ResourceLock object
                for resource_lock in resource_locks:
                    resource_lock.isLocked = True
                    resource_lock.acquiredByUri = acquired_by_uri
                    resource_lock.acquiredByType = acquired_by_type
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
    def release_lock(session, resource_uri, resource_type, share_uri):
        """
        Releases the lock on the resource identified by resource_uri, resource_type.

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
                        ResourceLock.isLocked,
                        ResourceLock.acquiredByUri == share_uri,
                    )
                )
                .with_for_update()
                .first()
            )

            if resource_lock:
                resource_lock.isLocked = False
                resource_lock.acquiredByUri = ''
                resource_lock.acquiredByType = ''

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
