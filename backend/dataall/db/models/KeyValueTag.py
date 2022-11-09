from sqlalchemy import Column, String, Boolean

from .. import Base
from .. import Resource, utils


class KeyValueTag(Base):
    __tablename__ = 'keyvaluetag'
    tagUri = Column(String, primary_key=True, default=utils.uuid('keyvaluetag'))
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    cascade = Column(Boolean, default=False)
