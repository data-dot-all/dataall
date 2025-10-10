"""add table for buckets

Revision ID: 8c79fb896983
Revises: 5781fdf1f877
Create Date: 2023-09-06 12:01:53.841149

"""

import os
from sqlalchemy import orm, Column, String, Boolean, ForeignKey, DateTime, inspect
from sqlalchemy.orm import query_expression
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from dataall.base.db import get_engine, has_table
from dataall.base.db import utils, Resource
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus
from datetime import datetime

from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language


# revision identifiers, used by Alembic.
revision = '8c79fb896983'
down_revision = '4f3c1d84a628'
branch_labels = None
depends_on = None

Base = declarative_base()


class Dataset(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    organizationUri = Column(String, nullable=False)
    datasetUri = Column(String, primary_key=True, default=utils.uuid('dataset'))
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=False)
    GlueCrawlerName = Column(String)
    GlueCrawlerSchedule = Column(String)
    GlueProfilingJobName = Column(String)
    GlueProfilingTriggerSchedule = Column(String)
    GlueProfilingTriggerName = Column(String)
    GlueDataQualityJobName = Column(String)
    GlueDataQualitySchedule = Column(String)
    GlueDataQualityTriggerName = Column(String)
    IAMDatasetAdminRoleArn = Column(String, nullable=False)
    IAMDatasetAdminUserArn = Column(String, nullable=False)
    KmsAlias = Column(String, nullable=False)
    userRoleForDataset = query_expression()
    userRoleInEnvironment = query_expression()
    isPublishedInEnvironment = query_expression()
    projectPermission = query_expression()
    language = Column(String, nullable=False, default=Language.English.value)
    topics = Column(postgresql.ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default=ConfidentialityClassification.Unclassified.value)
    tags = Column(postgresql.ARRAY(String))
    inProject = query_expression()

    bucketCreated = Column(Boolean, default=False)
    glueDatabaseCreated = Column(Boolean, default=False)
    iamAdminRoleCreated = Column(Boolean, default=False)
    iamAdminUserCreated = Column(Boolean, default=False)
    kmsAliasCreated = Column(Boolean, default=False)
    lakeformationLocationCreated = Column(Boolean, default=False)
    bucketPolicyCreated = Column(Boolean, default=False)

    # bookmarked = Column(Integer, default=0)
    # upvotes=Column(Integer, default=0)

    businessOwnerEmail = Column(String, nullable=True)
    businessOwnerDelegationEmails = Column(postgresql.ARRAY(String), nullable=True)
    stewards = Column(String, nullable=True)

    SamlAdminGroupName = Column(String, nullable=True)

    importedS3Bucket = Column(Boolean, default=False)
    importedGlueDatabase = Column(Boolean, default=False)
    importedKmsKey = Column(Boolean, default=False)
    importedAdminRole = Column(Boolean, default=False)
    imported = Column(Boolean, default=False)


class DatasetBucket(Resource, Base):
    __tablename__ = 'dataset_bucket'
    datasetUri = Column(String, nullable=False)
    bucketUri = Column(String, primary_key=True, default=utils.uuid('bucket'))
    AwsAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    partition = Column(String, default='aws')
    KmsAlias = Column(String, nullable=False)
    imported = Column(Boolean, default=False)
    importedKmsKey = Column(Boolean, default=False)
    userRoleForStorageBucket = query_expression()
    projectPermission = query_expression()
    environmentEndPoint = query_expression()

    @classmethod
    def uri_column(cls):
        return cls.bucketUri


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
        envname = os.getenv('envname', 'local')
        print('ENVNAME', envname)
        engine = get_engine(envname=envname).engine
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        datasets: [Dataset] = session.query(Dataset).all()
        if not has_table('dataset_bucket', engine):
            op.create_table(
                'dataset_bucket',
                sa.Column('bucketUri', sa.String(), nullable=False),
                sa.Column('label', sa.String(), nullable=False),
                sa.Column('name', sa.String(), nullable=False),
                sa.Column('owner', sa.String(), nullable=False),
                sa.Column('created', sa.DateTime(), nullable=True),
                sa.Column('updated', sa.DateTime(), nullable=True),
                sa.Column('deleted', sa.DateTime(), nullable=True),
                sa.Column('description', sa.String(), nullable=True),
                sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
                sa.Column('datasetUri', sa.String(), nullable=False),
                sa.Column('AwsAccountId', sa.String(), nullable=False),
                sa.Column('S3BucketName', sa.String(), nullable=False),
                sa.Column('KmsAlias', sa.String(), nullable=False),
                sa.Column('imported', sa.Boolean(), nullable=True),
                sa.Column('importedKmsKey', sa.Boolean(), nullable=True),
                sa.Column('region', sa.String(), nullable=True),
                sa.Column('partition', sa.String(), nullable=False, default='aws'),
                sa.ForeignKeyConstraint(columns=['datasetUri'], refcolumns=['dataset.datasetUri']),
                sa.PrimaryKeyConstraint('bucketUri'),
            )
            print('Creating a new dataset_bucket row for each existing dataset...')
            for dataset in datasets:
                dataset_bucket = DatasetBucket(
                    name=dataset.S3BucketName,
                    datasetUri=dataset.datasetUri,
                    AwsAccountId=dataset.AwsAccountId,
                    S3BucketName=dataset.S3BucketName,
                    region=dataset.region,
                    label=dataset.label,
                    description=dataset.label,
                    tags=dataset.tags,
                    owner=dataset.owner,
                    KmsAlias=dataset.KmsAlias,
                    imported=dataset.imported,
                    importedKmsKey=dataset.importedKmsKey,
                )
                session.add(dataset_bucket)
            session.flush()  # flush to get the bucketUri
        session.commit()

    except Exception as exception:
        print('Failed to upgrade due to:', exception)
        raise exception


def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c['name'] == column_name for c in columns)


def downgrade():
    op.drop_table('dataset_bucket')
