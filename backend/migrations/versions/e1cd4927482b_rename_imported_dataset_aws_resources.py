"""rename_imported_dataset_aws_resources

Revision ID: e1cd4927482b
Revises: 72b8a90b6ee8
Create Date: 2023-07-13 09:20:20.091639

"""

from alembic import op
from sqlalchemy import orm, Column, String, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils, Resource
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language

# revision identifiers, used by Alembic.
revision = 'e1cd4927482b'
down_revision = '72b8a90b6ee8'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = 'environment'
    organizationUri = Column(String, nullable=False)
    environmentUri = Column(String, primary_key=True, default=utils.uuid('environment'))
    AwsAccountId = Column(String, nullable=False)
    resourcePrefix = Column(String, nullable=False, default='dataall')


class Dataset(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, nullable=False)
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
    language = Column(String, nullable=False, default=Language.English.value)
    topics = Column(postgresql.ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default=ConfidentialityClassification.Unclassified.value)
    tags = Column(postgresql.ARRAY(String))

    bucketCreated = Column(Boolean, default=False)
    glueDatabaseCreated = Column(Boolean, default=False)
    iamAdminRoleCreated = Column(Boolean, default=False)
    iamAdminUserCreated = Column(Boolean, default=False)
    kmsAliasCreated = Column(Boolean, default=False)
    lakeformationLocationCreated = Column(Boolean, default=False)
    bucketPolicyCreated = Column(Boolean, default=False)

    businessOwnerEmail = Column(String, nullable=True)
    businessOwnerDelegationEmails = Column(postgresql.ARRAY(String), nullable=True)
    stewards = Column(String, nullable=True)

    SamlAdminGroupName = Column(String, nullable=True)

    importedS3Bucket = Column(Boolean, default=False)
    importedGlueDatabase = Column(Boolean, default=False)
    importedKmsKey = Column(Boolean, default=False)
    importedAdminRole = Column(Boolean, default=False)
    imported = Column(Boolean, default=False)


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Updating imported dataset aws resources names...')
        imported_datasets: [Dataset] = session.query(Dataset).filter(Dataset.imported.is_(True))
        for dataset in imported_datasets:
            print(f'Updating dataset {dataset.datasetUri}')
            environment: [Environment] = (
                session.query(Environment).filter(Environment.environmentUri == dataset.environmentUri).first()
            )
            glue_etl_basename = NamingConventionService(
                target_uri=dataset.datasetUri,
                target_label=dataset.label,
                pattern=NamingConventionPattern.GLUE_ETL,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name()
            dataset.GlueCrawlerName = f'{glue_etl_basename}-crawler'
            dataset.GlueProfilingJobName = f'{glue_etl_basename}-profiler'
            dataset.GlueProfilingTriggerName = f'{glue_etl_basename}-trigger'
            dataset.GlueDataQualityJobName = f'{glue_etl_basename}-dataquality'
            dataset.GlueDataQualityTriggerName = f'{glue_etl_basename}-dqtrigger'
            if not dataset.importedKmsKey:
                # Not adding downgrade for this line because this is a fix not an upgrade
                dataset.KmsAlias = 'Undefined'
            session.commit()
        print('imported Datasets resources updated successfully')
    except Exception as e:
        print(f'Failed to update imported dataset aws resources names due to: {e}')


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Updating imported dataset aws resources names to previous...')
        imported_datasets: [Dataset] = session.query(Dataset).filter(Dataset.imported.is_(True))
        for dataset in imported_datasets:
            print(f'Updating dataset {dataset.datasetUri}')
            glue_etl_basename = f'{dataset.S3BucketName}-{dataset.datasetUri}'
            dataset.GlueCrawlerName = f'{glue_etl_basename}-crawler'
            dataset.GlueProfilingJobName = f'{glue_etl_basename}-profiler'
            dataset.GlueProfilingTriggerName = f'{glue_etl_basename}-trigger'
            dataset.GlueDataQualityJobName = f'{glue_etl_basename}-dataquality'
            dataset.GlueDataQualityTriggerName = f'{glue_etl_basename}-dqtrigger'
            session.commit()
        print('imported Datasets resources updated successfully')
    except Exception as e:
        print(f'Failed to update imported dataset aws resources to previous names due to: {e}')
