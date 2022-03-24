import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base


from .utils import slugifier

Base = declarative_base()


class Resource(object):
    label = Column(String, nullable=False)
    name = Column(String, nullable=False, default=slugifier('label'))
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime, default=None)

    description = Column(String, default='No description provided')
    tags = Column(postgresql.ARRAY(String))
