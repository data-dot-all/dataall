"""_update_dataset_table_permissions

Revision ID: 0a267f6a5f05
Revises: 04d92886fabe
Create Date: 2022-12-21 08:58:22.287666

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, Column, String, Text, DateTime, and_
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from dataall.db import api, models, permissions, utils, Resource
from datetime import datetime
from dataall.db.models.Enums import ShareObjectStatus, ShareableType, PrincipalType

# revision identifiers, used by Alembic.
revision = '0a267f6a5f05'
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
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    action = Column(String, nullable=True)


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Re-Initializing permissions...')
        api.Permission.init_permissions(session)
        print('Permissions re-initialized successfully')
    except Exception as e:
        print(f'Failed to init permissions due to: {e}')

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Back-filling dataset table permissions...')
        dataset_tables: [DatasetTable] = session.query(DatasetTable).filter(
            models.DatasetTable.LastGlueTableStatus != "Deleted"
        ).all()
        for table in dataset_tables:
            dataset = api.Dataset.get_dataset_by_uri(session, table.datasetUri)
            env = api.Environment.get_environment_by_uri(session, dataset.environmentUri)

            groups = set([dataset.SamlAdminGroupName, env.SamlGroupName, dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName])
            for group in groups:
                api.ResourcePolicy.attach_resource_policy(
                    session=session,
                    resource_uri=table.tableUri,
                    group=group,
                    permissions=permissions.DATASET_TABLE_READ,
                    resource_type=models.DatasetTable.__name__,
                )
        print('dataset table permissions updated successfully for owners/stewards')
    except Exception as e:
        print(f'Failed to backfill dataset table permissions for owners/stewards due to: {e}')

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        share_table_items: [ShareObjectItem] = session.query(ShareObjectItem).filter(
            (
                and_(
                    models.ShareObjectItem.status == ShareObjectStatus.Approved.value,
                    models.ShareObjectItem.itemType == ShareableType.Table
                )
            )
        )
        for shared_table in share_table_items:
            share = api.ShareObject.get_share_by_uri(session, shared_table.shareUri)
            api.ResourcePolicy.attach_resource_policy(
                session=session,
                group=share.principalId,
                permissions=permissions.DATASET_TABLE_READ,
                resource_uri=shared_table.itemUri,
                resource_type=models.DatasetTable.__name__,
            )
        print('dataset table permissions updated for all shared tables')
    except Exception as e:
        print(f'Failed to update shared dataset table permissions due to: {e}')


def downgrade():
    pass
