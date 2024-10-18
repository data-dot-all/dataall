import logging
from datetime import datetime
from sqlalchemy import and_

from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemStatus,
    ShareableType,
)

logger = logging.getLogger(__name__)


class ShareStatusRepository:
    @staticmethod
    def get_share_item_shared_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Share_In_Progress.value,
            ShareItemStatus.Revoke_Failed.value,
            ShareItemStatus.Revoke_In_Progress.value,
            ShareItemStatus.Revoke_Approved.value,
        ]

    @staticmethod
    def get_share_item_revokable_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Revoke_Failed.value,
        ]

    @staticmethod
    def get_share_items_states(session, share_uri, item_uris=None):
        query = (
            session.query(ShareObjectItem)
            .join(
                ShareObject,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.shareUri == share_uri,
                )
            )
        )
        if item_uris:
            query = query.filter(ShareObjectItem.shareItemUri.in_(item_uris))
        return [item.status for item in query.distinct(ShareObjectItem.status)]

    @staticmethod
    def get_share_items_health_states(session, share_uri, item_uris=None):
        query = session.query(ShareObjectItem).filter(
            and_(
                ShareObjectItem.shareUri == share_uri,
            )
        )
        if item_uris:
            query = query.filter(ShareObjectItem.shareItemUri.in_(item_uris))
        return [item.healthStatus for item in query.distinct(ShareObjectItem.healthStatus)]

    @staticmethod
    def update_share_object_status(session, share_uri: str, status: str) -> ShareObject:
        share = ShareObjectRepository.get_share_by_uri(session, share_uri)
        share.status = status
        session.commit()
        return share

    @staticmethod
    def update_share_item_status(
        session,
        uri: str,
        status: str,
    ) -> ShareObjectItem:
        share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def update_share_item_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
        share_item_type: ShareableType = None,
    ) -> bool:
        query = session.query(ShareObjectItem).filter(
            and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == old_status)
        )
        if share_item_type:
            query = query.filter(ShareObjectItem.itemType == share_item_type.value)

        query.update(
            {
                ShareObjectItem.status: new_status,
            }
        )
        return True

    @staticmethod
    def delete_share_item_status_batch(
        session,
        share_uri: str,
        status: str,
    ):
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == status))
            .delete()
        )

    @staticmethod
    def delete_share_item_batch(
        session,
        share_uri: str,
    ):
        (session.query(ShareObjectItem).filter(and_(ShareObjectItem.shareUri == share_uri)).delete())

    @staticmethod
    def update_share_item_health_status(
        session,
        share_item: ShareObjectItem,
        healthStatus: str = None,
        healthMessage: str = None,
        timestamp: datetime = None,
    ) -> ShareObjectItem:
        share_item.healthStatus = healthStatus
        share_item.healthMessage = healthMessage
        share_item.lastVerificationTime = timestamp
        session.commit()
        return share_item

    @staticmethod
    def update_share_item_health_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
        message: str = None,
    ) -> bool:
        query = session.query(ShareObjectItem).filter(
            and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.healthStatus == old_status)
        )

        if message:
            query.update(
                {
                    ShareObjectItem.healthStatus: new_status,
                    ShareObjectItem.healthMessage: message,
                    ShareObjectItem.lastVerificationTime: datetime.now(),
                }
            )
        else:
            query.update(
                {
                    ShareObjectItem.healthStatus: new_status,
                }
            )
        return True

    @staticmethod
    def count_items_in_states(session, uri, states):
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == uri,
                    ShareObjectItem.status.in_(states),
                )
            )
            .count()
        )

    @staticmethod
    def check_pending_share_items(session, uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    ShareObjectItem.status.in_([ShareItemStatus.PendingApproval.value]),
                )
            )
            .all()
        )
        return bool(shared_items)

    @staticmethod
    def check_existing_shared_items(session, uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(ShareObjectItem.shareUri == share.shareUri, ShareObjectItem.status.in_(share_item_shared_states))
            )
            .all()
        )
        return bool(shared_items)
