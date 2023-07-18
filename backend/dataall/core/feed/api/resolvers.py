from sqlalchemy import or_

from dataall.api.context import Context
from dataall.core.feed.db.feed_models import FeedMessage
from dataall.base.db import paginate
from dataall.core.feed.api.registry import FeedRegistry


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


def resolve_feed_target_type(obj, *_):
    return FeedRegistry.find_target(obj)


def resolve_target(context: Context, source: Feed, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        model = FeedRegistry.find_model(source.targetType)
        target = session.query(model).get(source.targetUri)
    return target


def get_feed(
    context: Context,
    source,
    targetUri: str = None,
    targetType: str = None,
    filter: dict = None,
) -> Feed:
    return Feed(targetUri=targetUri, targetType=targetType)


def post_message(
    context: Context,
    source,
    targetUri: str = None,
    targetType: str = None,
    input: dict = None,
):
    with context.engine.scoped_session() as session:
        m = FeedMessage(
            targetUri=targetUri,
            targetType=targetType,
            creator=context.username,
            content=input.get('content'),
        )
        session.add(m)
    return m


def resolve_messages(context: Context, source: Feed, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = session.query(FeedMessage).filter(
            FeedMessage.targetUri == source.targetUri
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    FeedMessage.content.ilike('%' + term + '%'),
                    FeedMessage.creator.ilike('%' + term + '%'),
                )
            )
        q = q.order_by(FeedMessage.created.desc())

    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)
    ).to_dict()
