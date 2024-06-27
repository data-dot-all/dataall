"""backfill_dataset_table_permissions

Revision ID: d05f9a5b215e
Revises: 04d92886fabe
Create Date: 2022-12-22 10:18:55.835315

"""

from alembic import op
from sqlalchemy import orm, Column, String, Text, DateTime, and_
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.base.db import utils, Resource
from datetime import datetime

from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectStatus,
    ShareableType,
    ShareItemStatus,
)
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_TABLE_READ

# revision identifiers, used by Alembic.
revision = 'd05f9a5b215e'
down_revision = '04d92886fabe'
branch_labels = None
depends_on = None

Base = declarative_base()


class DatasetTable(Resource, Base):
    __tablename__ = 'dataset_table'
    datasetUri = Column(String, nullable=False)
    tableUri = Column(String, primary_key=True, default=utils.uuid('table'))
    AWSAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    S3Prefix = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=False)
    GlueTableName = Column(String, nullable=False)
    GlueTableConfig = Column(Text)
    GlueTableProperties = Column(postgresql.JSON, default={})
    LastGlueTableStatus = Column(String, default='InSync')
    region = Column(String, default='eu-west-1')
    # LastGeneratedPreviewDate= Column(DateTime, default=None)
    confidentiality = Column(String, nullable=True)
    userRoleForTable = query_expression()
    projectPermission = query_expression()
    redshiftClusterPermission = query_expression()
    stage = Column(String, default='RAW')
    topics = Column(postgresql.ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default='C1')


class ShareObjectItem(Base):
    __tablename__ = 'share_object_item'
    shareUri = Column(String, nullable=False)
    shareItemUri = Column(String, default=utils.uuid('shareitem'), nullable=False, primary_key=True)
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
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    action = Column(String, nullable=True)


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Re-Initializing permissions...')
        PermissionService.init_permissions(session)
        print('Permissions re-initialized successfully')
    except Exception as e:
        print(f'Failed to init permissions due to: {e}')

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Back-filling dataset table permissions for owners/stewards...')
        dataset_tables: [DatasetTable] = session.query(DatasetTable).filter(DatasetTable.deleted.is_(None)).all()
        for table in dataset_tables:
            dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)

            groups = {
                dataset.SamlAdminGroupName,
                env.SamlGroupName,
                dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName,
            }
            for group in groups:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    resource_uri=table.tableUri,
                    group=group,
                    permissions=DATASET_TABLE_READ,
                    resource_type=DatasetTable.__name__,
                )
        print('dataset table permissions updated successfully for owners/stewards')
    except Exception as e:
        print(f'Failed to backfill dataset table permissions for owners/stewards due to: {e}')

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Back-filling dataset table permissions for shared principals...')
        share_table_items: [ShareObjectItem] = (
            session.query(ShareObjectItem)
            .filter(
                (
                    and_(
                        ShareObjectItem.status == ShareItemStatus.Share_Succeeded.value,
                        ShareObjectItem.itemType == ShareableType.Table.value,
                    )
                )
            )
            .all()
        )
        for shared_table in share_table_items:
            share = ShareObjectRepository.get_share_by_uri(session, shared_table.shareUri)
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.principalId,
                permissions=DATASET_TABLE_READ,
                resource_uri=shared_table.itemUri,
                resource_type=DatasetTable.__name__,
            )
        print('dataset table permissions updated for all shared tables')
    except Exception as e:
        print(f'Failed to update shared dataset table permissions due to: {e}')


def downgrade():
    pass
