from sqlalchemy import Column, String

from .. import Base
from .. import Resource, utils


class Activity(Resource, Base):
    __tablename__ = "activity"
    activityUri = Column(String, primary_key=True, default=utils.uuid("activity"))
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
    action = Column(String, nullable=False)
    summary = Column(String, nullable=False)
