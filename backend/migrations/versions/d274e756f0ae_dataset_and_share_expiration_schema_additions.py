"""describe_changes_shortly

Revision ID: d274e756f0ae
Revises: 797dd1012be1
Create Date: 2024-07-18 14:25:20.728900

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, ForeignKey, ARRAY, Boolean, Enum, orm, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import query_expression

from dataall.base.db import Resource, utils
from dataall.core.environment.api.enums import EnvironmentType
from dataall.modules.datasets_base.services.datasets_enums import Language, ConfidentialityClassification, DatasetTypes

# revision identifiers, used by Alembic.
revision = 'd274e756f0ae'
down_revision = '797dd1012be1'
branch_labels = None
depends_on = None

Base = declarative_base()

class DatasetBase(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    organizationUri = Column(String, nullable=False)
    datasetUri = Column(String, primary_key=True, default=utils.uuid('dataset'))
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    userRoleForDataset = query_expression()
    userRoleInEnvironment = query_expression()
    isPublishedInEnvironment = query_expression()
    projectPermission = query_expression()
    language = Column(String, nullable=False, default=Language.English.value)
    topics = Column(ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default=ConfidentialityClassification.Unclassified.value)
    tags = Column(ARRAY(String))
    inProject = query_expression()
    businessOwnerEmail = Column(String, nullable=True)
    businessOwnerDelegationEmails = Column(ARRAY(String), nullable=True)
    stewards = Column(String, nullable=True)
    SamlAdminGroupName = Column(String, nullable=True)
    autoApprovalEnabled = Column(Boolean, default=False)
    datasetType = Column(Enum(DatasetTypes), nullable=False, default=DatasetTypes.S3)
    imported = Column(Boolean, default=False)
    enableExpiration = Column(Boolean, default=False, nullable=False)
    expiryMinDuration = Column(Integer, nullable=True)
    expiryMaxDuration = Column(Integer, nullable=True)
    __mapper_args__ = {'polymorphic_identity': 'dataset', 'polymorphic_on': datasetType}


class S3Dataset(DatasetBase):
    __tablename__ = 's3_dataset'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), primary_key=True)
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
    bucketCreated = Column(Boolean, default=False)
    glueDatabaseCreated = Column(Boolean, default=False)
    iamAdminRoleCreated = Column(Boolean, default=False)
    iamAdminUserCreated = Column(Boolean, default=False)
    kmsAliasCreated = Column(Boolean, default=False)
    lakeformationLocationCreated = Column(Boolean, default=False)
    bucketPolicyCreated = Column(Boolean, default=False)
    importedS3Bucket = Column(Boolean, default=False)
    importedGlueDatabase = Column(Boolean, default=False)
    importedKmsKey = Column(Boolean, default=False)
    importedAdminRole = Column(Boolean, default=False)
    __mapper_args__ = {
        'polymorphic_identity': DatasetTypes.S3,
    }


class Environment(Resource, Base):
    __tablename__ = 'environment'
    organizationUri = Column(String, nullable=False)
    environmentUri = Column(String, primary_key=True, default=utils.uuid('environment'))
    AwsAccountId = Column(String, nullable=False)
    region = Column(String, nullable=False, default='eu-west-1')
    cognitoGroupName = Column(String, nullable=True)
    resourcePrefix = Column(String, nullable=False, default='dataall')

    validated = Column(Boolean, default=False)
    environmentType = Column(String, nullable=False, default=EnvironmentType.Data.value)
    isOrganizationDefaultEnvironment = Column(Boolean, default=False)
    EnvironmentDefaultIAMRoleName = Column(String, nullable=False)
    EnvironmentDefaultIAMRoleImported = Column(Boolean, default=False)
    EnvironmentDefaultIAMRoleArn = Column(String, nullable=False)
    EnvironmentDefaultBucketName = Column(String)
    EnvironmentDefaultAthenaWorkGroup = Column(String)
    roleCreated = Column(Boolean, nullable=False, default=False)

    userRoleInEnvironment = query_expression()

    SamlGroupName = Column(String, nullable=True)
    CDKRoleArn = Column(String, nullable=False)

    subscriptionsEnabled = Column(Boolean, default=False)
    subscriptionsProducersTopicName = Column(String)
    subscriptionsProducersTopicImported = Column(Boolean, default=False)
    subscriptionsConsumersTopicName = Column(String)
    subscriptionsConsumersTopicImported = Column(Boolean, default=False)




def upgrade():
    # Add Columns to the dataset base table
    op.add_column('dataset', sa.Column('enableExpiration', sa.Boolean(), nullable=False, default=False, server_default=sa.sql.expression.false()))
    op.add_column('dataset', sa.Column('expiryMinDuration', sa.Integer(), nullable=True))
    op.add_column('dataset', sa.Column('expiryMaxDuration', sa.Integer(), nullable=True))

    # Backfill the expiration columns for all currently onboarded datasets
    # try:
    #     bind = op.get_bind()
    #     session = orm.Session(bind=bind)
    #     print('Back-filling datasets with enableExpiration column set to False')
    #     datasets: [DatasetBase] = session.query(DatasetBase)
    #     for dataset in datasets:
    #         dataset.enableExpiration = False
    #     session.commit()
    #     print('Updated dataset column enableExpiration to False for all datasets')
    #
    # except Exception as e:
    #     print(f'Failed to back-fill dataset after dataset expiration schema changes due to - {e}')




def downgrade():
    op.drop_column('dataset', 'enableExpiration')
    op.drop_column('dataset', 'expiryMinDuration')
    op.drop_column('dataset', 'expiryMaxDuration')
