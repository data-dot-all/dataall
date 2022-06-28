from sqlalchemy import Column, String
from .. import Base, Resource, utils


class ShareObjectHistory(Resource, Base):
    __tablename__ = "share_object_history"
    historyUri = Column(String, primary_key=True, default=utils.uuid("share_history"))
    shareUri = Column(String, nullable=False)
    actionName = Column(String, nullable=False)
