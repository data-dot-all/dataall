import logging
from sqlalchemy import and_

from dataall.base.db import exceptions
from dataall.modules.s3_datasets_shares.db.share_object_models import ShareObjectItem, ShareObject

logger = logging.getLogger(__name__)


class ShareObjectRepository:  # Slowly moving db models and repositories to shares_base
    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def update_share_object_status(session, share_uri: str, status: str) -> ShareObject:
        share = ShareObjectRepository.get_share_by_uri(session, share_uri)
        share.status = status
        session.commit()
        return share

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
    def update_share_item_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == old_status))
            .update(
                {
                    ShareObjectItem.status: new_status,
                }
            )
        )
        return True
