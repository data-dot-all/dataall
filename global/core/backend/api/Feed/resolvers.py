from sqlalchemy import or_

from ....api.context import Context
from ....db import paginate, models


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
    if isinstance(obj, models.DatasetTableColumn):
        return 'DatasetTableColumn'
    elif isinstance(obj, models.Worksheet):
        return 'Worksheet'
    elif isinstance(obj, models.DataPipeline):
        return 'DataPipeline'
    elif isinstance(obj, models.DatasetTable):
        return 'DatasetTable'
    elif isinstance(obj, models.Dataset):
        return 'Dataset'
    elif isinstance(obj, models.DatasetStorageLocation):
        return 'DatasetStorageLocation'
    elif isinstance(obj, models.Dashboard):
        return 'Dashboard'
    else:
        return None


def resolve_target(context: Context, source: Feed, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        model = {
            'Dataset': models.Dataset,
            'DatasetTable': models.DatasetTable,
            'DatasetTableColumn': models.DatasetTableColumn,
            'DatasetStorageLocation': models.DatasetStorageLocation,
            'Dashboard': models.Dashboard,
            'DataPipeline': models.DataPipeline,
            'Worksheet': models.Worksheet,
        }[source.targetType]
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
        m = models.FeedMessage(
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
        q = session.query(models.FeedMessage).filter(
            models.FeedMessage.targetUri == source.targetUri
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    models.FeedMessage.content.ilike('%' + term + '%'),
                    models.FeedMessage.creator.ilike('%' + term + '%'),
                )
            )
        q = q.order_by(models.FeedMessage.created.desc())

    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)
    ).to_dict()
