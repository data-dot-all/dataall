"""
A service layer for Feeds
Central part for working with Feeds
"""

import logging

from dataall.base.context import get_context
from dataall.modules.feed.db.feed_models import FeedMessage
from dataall.modules.feed.db.feed_repository import FeedRepository


logger = logging.getLogger(__name__)


class Feed:
    def __init__(self, targetUri: str = None, targetType: str = None):
        self._targetUri = targetUri
        self._targetType = targetType

    @property
    def targetUri(self):
        return self._targetUri

    @property
    def targetType(self):
        return self._targetType


def _session():
    return get_context().db_engine.scoped_session()


class FeedService:
    """
    Encapsulate the logic of interactions with Feeds.
    """

    @staticmethod
    def get_feed(
        targetUri: str = None,
        targetType: str = None,
    ) -> Feed:
        return Feed(targetUri=targetUri, targetType=targetType)

    @staticmethod
    def post_feed_message(
        targetUri: str = None,
        targetType: str = None,
        content: str = None,
    ):
        with _session() as session:
            m = FeedMessage(
                targetUri=targetUri,
                targetType=targetType,
                creator=get_context().username,
                content=content,
            )
            session.add(m)
        return m

    @staticmethod
    def list_feed_messages(targetUri: str, filter: dict = None):
        with _session() as session:
            return FeedRepository(session).paginated_feed_messages(uri=targetUri, filter=filter)
