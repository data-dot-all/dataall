import datetime

from sqlalchemy import Column, DateTime, String
from enum import Enum

from .. import Base

class GroupMemberRole(Enum):
    Owner = 'Owner'
    Admin = 'Admin'
    Member = 'Member'
    NotMember = 'NotMember'


class GroupMember(Base):
    __tablename__ = 'group_member'
    groupUri = Column(String, primary_key=True)
    userName = Column(String, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)

    userRoleInGroup = Column(
        String, nullable=False, default=GroupMemberRole.Member.value
    )
