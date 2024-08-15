"""add_data_filters_table

Revision ID: 9efe5f7c69a1
Revises: afcfc928c640
Create Date: 2024-07-17 11:05:26.077658

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, orm
from sqlalchemy.dialects import postgresql
from dataall.base.db import Resource, utils
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.api.enums import PermissionType
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_TABLE_DATA_FILTERS, DATASET_TABLE_READ
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = '9efe5f7c69a1'
down_revision = 'afcfc928c640'
branch_labels = None
depends_on = None

Base = declarative_base()


class DatasetBase(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    organizationUri = Column(String, nullable=False)
    datasetUri = Column(String, primary_key=True, default=utils.uuid('dataset'))
    stewards = Column(String, nullable=True)
    SamlAdminGroupName = Column(String, nullable=True)
    datasetType = Column(Enum(DatasetTypes), nullable=False, default=DatasetTypes.S3)

    __mapper_args__ = {'polymorphic_identity': 'dataset', 'polymorphic_on': datasetType}


class S3Dataset(DatasetBase):
    __tablename__ = 's3_dataset'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': DatasetTypes.S3,
    }


class DatasetTable(Resource, Base):
    __tablename__ = 'dataset_table'
    datasetUri = Column(String, nullable=False)
    tableUri = Column(String, primary_key=True, default=utils.uuid('table'))


def upgrade():
    op.create_table(
        'data_filter',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('filterUri', sa.String(), nullable=False),
        sa.Column('tableUri', sa.String(), nullable=False),
        sa.Column('filterType', sa.String(), nullable=False),
        sa.Column('includedCols', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('rowExpression', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['tableUri'], ['dataset_table.tableUri'], name='data_filter_tableUri_fkey'),
        sa.PrimaryKeyConstraint('filterUri'),
    )

    op.create_table(
        'share_object_item_data_filter',
        sa.Column('attachedDataFilterUri', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('itemUri', sa.String(), nullable=False),
        sa.Column('dataFilterUris', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('dataFilterNames', postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint('attachedDataFilterUri'),
        sa.Index('ix_itemUri_label', 'itemUri', 'label', unique=True),
    )

    op.add_column('share_object_item', sa.Column('attachedDataFilterUri', sa.String(), nullable=True))
    op.create_foreign_key(
        'share_object_item_attachedDataFilterUri_fkey',
        'share_object_item',
        'share_object_item_data_filter',
        ['attachedDataFilterUri'],
        ['attachedDataFilterUri'],
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    print('Adding DATASET_TABLE_DATA_FILTERS permissions for all s3 dataset tables...')
    for perm in DATASET_TABLE_DATA_FILTERS:
        PermissionService.save_permission(
            session,
            name=perm,
            description=perm,
            permission_type=PermissionType.RESOURCE.name,
        )
    s3_datasets: [S3Dataset] = session.query(S3Dataset).all()
    for dataset in s3_datasets:
        dataset_tables = session.query(DatasetTable).filter(DatasetTable.datasetUri == dataset.datasetUri).all()
        for table in dataset_tables:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                resource_uri=table.tableUri,
                permissions=DATASET_TABLE_DATA_FILTERS,
                resource_type=DatasetTable.__name__,
            )
            if dataset.stewards is not None and dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=table.tableUri,
                    permissions=DATASET_TABLE_DATA_FILTERS,
                    resource_type=DatasetTable.__name__,
                )
    # ### end Alembic commands ###


def downgrade():
    op.drop_constraint('share_object_item_attachedDataFilterUri_fkey', 'share_object_item', type_='foreignkey')
    op.drop_column('share_object_item', 'attachedDataFilterUri')
    op.drop_index('ix_itemUri_label', table_name='share_object_item_data_filter')
    op.drop_table('share_object_item_data_filter')
    op.drop_table('data_filter')

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    print('Removing DATASET_TABLE_DATA_FILTERS permissions for all s3 dataset tables...')
    s3_datasets: [S3Dataset] = session.query(S3Dataset).all()
    for dataset in s3_datasets:
        dataset_tables = session.query(DatasetTable).filter(DatasetTable.datasetUri == dataset.datasetUri).all()
        for table in dataset_tables:
            ResourcePolicyService.update_resource_policy(
                session=session,
                resource_uri=table.tableUri,
                resource_type=DatasetTable.__name__,
                old_group=dataset.SamlAdminGroupName,
                new_group=dataset.SamlAdminGroupName,
                new_permissions=DATASET_TABLE_READ,
            )
            if dataset.stewards is not None and dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicyService.update_resource_policy(
                    session=session,
                    resource_uri=table.tableUri,
                    resource_type=DatasetTable.__name__,
                    old_group=dataset.stewards,
                    new_group=dataset.stewards,
                    new_permissions=DATASET_TABLE_READ,
                )

    # ### end Alembic commands ###
