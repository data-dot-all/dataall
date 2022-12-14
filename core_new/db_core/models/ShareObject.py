from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.orm import query_expression

from enum import Enum

from backend.db.common import Base, utils


class ShareObjectPermission(Enum):
    Approvers = '999'
    Requesters = '800'
    DatasetAdmins = '700'
    NoPermission = '000'


class ShareObjectStatus(Enum):
    Approved = 'Approved'
    Rejected = 'Rejected'
    PendingApproval = 'PendingApproval'
    Draft = 'Draft'
    Share_In_Progress = 'Share_In_Progress'
    Share_Failed = 'Share_Failed'
    Share_Succeeded = 'Share_Succeeded'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Revoke_Share_Failed = 'Revoke_Share_Failed'
    Revoke_Share_Succeeded = 'Revoke_Share_Succeeded'


class ShareableType(Enum):
    Table = 'DatasetTable'
    StorageLocation = 'DatasetStorageLocation'
    View = 'View'


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
    principalId = Column(String, nullable=True)
    principalType = Column(String, nullable=True, default='GROUP')
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    userRoleForShareObject = query_expression()
