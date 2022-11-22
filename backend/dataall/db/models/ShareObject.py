from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.orm import query_expression

from .Enums import ShareObjectStatus
from .. import Base, utils


def in_one_month():
    return datetime.now() + timedelta(days=31)


def _uuid4():
    return str(uuid4())


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('share')
    )
    datasetUri = Column(String, nullable=False)
    environmentUri = Column(String)
    groupUri = Column(String)
    principalIAMRoleName = Column(String, nullable=True)
    principalId = Column(String, nullable=True)
    principalType = Column(String, nullable=True, default='Group')
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    userRoleForShareObject = query_expression()
