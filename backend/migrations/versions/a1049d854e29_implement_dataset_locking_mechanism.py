"""implement_resource_locking_mechanism

Revision ID: a1049d854e29
Revises: 6c9a8afee4e4
Create Date: 2024-02-01 16:38:32.533228

"""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Boolean, Column, String, orm, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from dataall.base.db import get_engine, has_table
from dataall.base.db import utils, Resource
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1049d854e29'
down_revision = '6c9a8afee4e4'
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
    language = Column(String, nullable=False, default='English')
    topics = Column(postgresql.ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default='Unclassified')
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


class DatasetLock(Base):
    __tablename__ = 'dataset_lock'
    datasetUri = Column(String, nullable=False, primary_key=True)
    isLocked = Column(Boolean, default=False, nullable=False)
    acquiredBy = Column(String, nullable=True)

    @classmethod
    def uri_column(cls):
        return cls.datasetUri


def upgrade():
    """
    The script does the following migration:
        1) creation of the dataset_lock table
    """
    try:
        envname = os.getenv('envname', 'local')
        print('ENVNAME', envname)
        engine = get_engine(envname=envname).engine

        bind = op.get_bind()
        session = orm.Session(bind=bind)
        datasets: [Dataset] = session.query(Dataset).all()

        if not has_table('dataset_lock', engine):
            print('Creating dataset_lock table')

            op.create_table(
                'dataset_lock',
                sa.Column('datasetUri', sa.String(), primary_key=True),
                sa.Column('isLocked', sa.Boolean(), nullable=False),
                sa.Column('acquiredBy', sa.String(), nullable=True),
            )

            op.create_foreign_key(
                'fk_dataset_lock_datasetUri',  # Constraint name
                'dataset_lock',
                'dataset',
                ['datasetUri'],
                ['datasetUri'],
            )

            print('Creating a new row for each existing dataset in dataset_lock table')
            for dataset in datasets:
                dataset_lock = DatasetLock(datasetUri=dataset.datasetUri, isLocked=False, acquiredBy='')
                session.add(dataset_lock)
            session.flush()  # flush to get the datasetUri

        print('Creation of dataset_lock table is done')

        session.commit()

    except Exception as ex:
        print(f'Failed to execute the migration script due to: {ex}')
        raise ex


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Dropping dataset_lock table')

        op.drop_table('dataset_lock')

        print('Dropping of dataset_lock table is done')
        session.commit()

    except Exception as ex:
        print(f'Failed to execute the migration script due to: {ex}')
        raise ex
