from dataall.base.db import Base
from sqlalchemy import String, Integer, Column, Date, func
import uuid


class ResourceTreshold(Base):
    __tablename__ = 'resource_treshold'
    actionId = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), nullable=False)
    actionType = Column(String(64), nullable=False)
    date = Column(Date, default=func.current_date(), nullable=False)
    count = Column(Integer, default=1, nullable=False)

