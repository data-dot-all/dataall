from sqlalchemy import Column, String

from dataall.base.db import Base, Resource, utils


class Group(Resource, Base):
    __tablename__ = 'group'
    groupUri = Column(String, primary_key=True, default=utils.uuid('group'))
