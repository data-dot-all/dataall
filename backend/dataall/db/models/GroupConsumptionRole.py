import datetime

from sqlalchemy import Column, String, DateTime

from .. import Base, Resource, utils


class GroupConsumptionRole(Base):
    __tablename__ = 'groupconsumptionrole'
    groupConsumptionRoleUri = Column(String, primary_key=True, default=utils.uuid('group'))
    consumptionRoleName = Column(String, nullable=False)
    environmentUri = Column(String, nullable=False)
    groupUri = Column(String, nullable=False)
    IAMRoleArn = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
