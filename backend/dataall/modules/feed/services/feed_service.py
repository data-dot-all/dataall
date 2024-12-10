"""
A service layer for Feeds
Central part for working with Feeds
"""

import logging

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.feed.db.feed_models import FeedMessage
from dataall.modules.feed.db.feed_repository import FeedRepository
from dataall.modules.feed.api.registry import FeedRegistry


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


class FeedService:
    """
    Encapsulate the logic of interactions with Feeds.
    """

    @staticmethod
    def get_feed(
        targetUri: str = None,
        targetType: str = None,
    ) -> Feed:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=targetUri,
                permission_name=FeedRegistry.find_permission(target_type=targetType),
            )
        return Feed(targetUri=targetUri, targetType=targetType)

    @staticmethod
    def post_feed_message(
        targetUri: str = None,
        targetType: str = None,
        content: str = None,
    ):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=targetUri,
                permission_name=FeedRegistry.find_permission(target_type=targetType),
            )
            m = FeedMessage(
                targetUri=targetUri,
                targetType=targetType,
                creator=context.username,
                content=content,
            )
            session.add(m)
        return m

    @staticmethod
    def list_feed_messages(targetUri: str, targetType: str, filter: dict = None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=targetUri,
                permission_name=FeedRegistry.find_permission(target_type=targetType),
            )
            return FeedRepository(session).paginated_feed_messages(uri=targetUri, filter=filter)
