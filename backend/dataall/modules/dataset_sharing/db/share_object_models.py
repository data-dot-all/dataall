from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.orm import query_expression

from dataall.base.db import Base, utils
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import ShareObjectStatus, ShareItemStatus

from dataall.modules.dataset_sharing.aws.glue_client import GlueClient


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
    requestPurpose = Column(String, nullable=True)
    rejectPurpose = Column(String, nullable=True)
    userRoleForShareObject = query_expression()
    existingSharedItems = query_expression()


class ShareObjectItem(Base):
    __tablename__ = 'share_object_item'
    shareUri = Column(String, nullable=False)
    shareItemUri = Column(
        String, default=utils.uuid('shareitem'), nullable=False, primary_key=True
    )
    itemType = Column(String, nullable=False)
    itemUri = Column(String, nullable=False)
    itemName = Column(String, nullable=False)
    permission = Column(String, nullable=True)
    created = Column(DateTime, nullable=False, default=datetime.now)
    updated = Column(DateTime, nullable=True, onupdate=datetime.now)
    deleted = Column(DateTime, nullable=True)
    owner = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=True)
    GlueTableName = Column(String, nullable=True)
    S3AccessPointName = Column(String, nullable=True)
    status = Column(String, nullable=False, default=ShareItemStatus.PendingApproval.value)
    action = Column(String, nullable=True)

    def build_shared_db_name(self, account_id, region):
        """
        It checks if a share is prior to 2.3.0 and builds its suffix as "_shared_" + shareUri
        For shares after 2.3.0 the suffix returned is "_shared"
        :return: Shared database name
        """
        old_shared_db_name = (self.GlueDatabaseName + '_shared_' + self.shareUri)[:254]
        database = GlueClient(
            account_id=account_id,
            database=old_shared_db_name,
            region=region
        ).get_glue_database()

        if database:
            return old_shared_db_name
        return self.GlueDatabaseName + '_shared'
