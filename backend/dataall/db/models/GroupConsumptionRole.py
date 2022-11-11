from sqlalchemy import Column, String

from .. import Base, Resource, utils


class GroupConsumptionRole(Resource, Base):
    __tablename__ = 'groupconsumptionrole'
    groupConsumptionRoleUri = Column(String, primary_key=True, default=utils.uuid('group'))
    consumptionRoleName = Column(String, nullable=False)
    environmentUri = Column(String, nullable=False)
    groupUri = Column(String, nullable=False)
    IAMRoleArn = Column(String, nullable=False)
