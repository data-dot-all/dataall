from datetime import datetime

from sqlalchemy import Column, DateTime, String

from .. import Base
from .. import utils


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(String, primary_key=True, default=utils.uuid('tag'))
    tag = Column(String, nullable=False)
    owner = Column(String)
    created = Column(DateTime, default=datetime.now)


class ItemTags(Base):
    __tablename__ = 'item_tags'
    tagid = Column(String, primary_key=True)
    itemid = Column(String, primary_key=True)


def updateObjectTags(session, username, uri: str = None, tags=[]):
    ids = {}
    session.query(ItemTags).filter(ItemTags.itemid == uri).delete()
    if tags:
        for t in set(tags or []):
            exists = session.query(Tag).filter(Tag.tag == t).first()
            if exists:
                id = exists.id
            else:
                id = utils.uuid('tag')(None)
                tag = Tag(id=id, tag=t, owner=username)
                session.add(tag)
                session.commit()
            link = ItemTags(tagid=id, itemid=uri)
            session.add(link)
