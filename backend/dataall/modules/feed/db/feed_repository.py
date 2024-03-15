"""
DAO layer that encapsulates the logic and interaction with the database for Feeds
Provides the API to retrieve / update / delete FeedS
"""

from sqlalchemy import or_

from dataall.base.db import paginate
from dataall.modules.feed.db.feed_models import FeedMessage


class FeedRepository:
    def __init__(self, session):
        self._session = session

    def paginated_feed_messages(self, uri, filter):
        q = self._session.query(FeedMessage).filter(FeedMessage.targetUri == uri)
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    FeedMessage.content.ilike('%' + term + '%'),
                    FeedMessage.creator.ilike('%' + term + '%'),
                )
            )
        q = q.order_by(FeedMessage.created.desc())

        return paginate(q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)).to_dict()
