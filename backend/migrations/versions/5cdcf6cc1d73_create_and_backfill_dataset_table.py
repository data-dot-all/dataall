"""create_and_backfill_dataset_table

Revision ID: 5cdcf6cc1d73
Revises: d059eead99c2
Create Date: 2024-05-07 15:24:09.833007

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import query_expression
from dataall.base.db import utils, Resource
from sqlalchemy.ext.declarative import declarative_base
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes

# revision identifiers, used by Alembic.
revision = '5cdcf6cc1d73'
down_revision = 'd059eead99c2'
branch_labels = None
depends_on = None


def upgrade():
    print('Creating dataset table...')
    new_dataset_table = op.create_table(
        'dataset',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('environmentUri', sa.String(), nullable=False),
        sa.Column('organizationUri', sa.String(), nullable=False),
        sa.Column('datasetUri', sa.String(), nullable=False),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('AwsAccountId', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('confidentiality', sa.String(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('businessOwnerEmail', sa.String(), nullable=True),
        sa.Column('businessOwnerDelegationEmails', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('stewards', sa.String(), nullable=True),
        sa.Column('SamlAdminGroupName', sa.String(), nullable=True),
        sa.Column('autoApprovalEnabled', sa.Boolean(), default=False),
        sa.Column(
            'datasetType',
            postgresql.ENUM(DatasetTypes.S3.value, name='datasettypes', create_type=False),
            nullable=False,
        ),
        sa.Column('imported', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(
            ['environmentUri'],
            ['environment.environmentUri'],
        ),
        sa.PrimaryKeyConstraint('datasetUri'),
    )
    print('Backfill dataset with s3_dataset data...')
    # Read s3_datasets table rows
    conn = op.get_bind()
    res = conn.execute(
        'select label, name, owner, created, updated, deleted, description, "environmentUri", "organizationUri", "datasetUri", region, "AwsAccountId",  "language", topics, confidentiality, tags, "businessOwnerEmail", "businessOwnerDelegationEmails", stewards, "SamlAdminGroupName", "autoApprovalEnabled", "datasetType", imported  from s3_dataset'
    )
    results = res.fetchall()
    s3_datasets_info = [
        {
            'label': r[0],
            'name': r[1],
            'owner': r[2],
            'created': r[3],
            'updated': r[4],
            'deleted': r[5],
            'description': r[6],
            'environmentUri': r[7],
            'organizationUri': r[8],
            'datasetUri': r[9],
            'region': r[10],
            'AwsAccountId': r[11],
            'language': r[12],
            'topics': r[13],
            'confidentiality': r[14],
            'tags': r[15],
            'businessOwnerEmail': r[16],
            'businessOwnerDelegationEmails': r[17],
            'stewards': r[18],
            'SamlAdminGroupName': r[19],
            'autoApprovalEnabled': r[20],
            'datasetType': r[21],
            'imported': r[22],
        }
        for r in results
    ]

    # Insert s3_datasets_info into new datasets table.
    op.bulk_insert(new_dataset_table, s3_datasets_info)

    # Update foreign keys
    op.create_foreign_key('dataset_datasetUri_fkey', 's3_dataset', 'dataset', ['datasetUri'], ['datasetUri'])

    # Update foreign keys of dataset_bucket -> to s3_dataset and dataset_lock -> to dataset tables
    op.drop_constraint('fk_dataset_lock_datasetUri', 'dataset_lock', type_='foreignkey')
    op.create_foreign_key('dataset_lock_datasetUri_fkey', 'dataset_lock', 'dataset', ['datasetUri'], ['datasetUri'])

    op.drop_constraint('dataset_bucket_datasetUri_fkey', 'dataset_bucket', type_='foreignkey')
    op.create_foreign_key(
        's3_dataset_bucket_datasetUri_fkey',
        'dataset_bucket',
        's3_dataset',
        ['datasetUri'],
        ['datasetUri'],
        ondelete='CASCADE',
    )

    # drop columns generic columns from s3_datasets_table
    op.drop_column('s3_dataset', 'label')
    op.drop_column('s3_dataset', 'name')
    op.drop_column('s3_dataset', 'owner')
    op.drop_column('s3_dataset', 'created')
    op.drop_column('s3_dataset', 'updated')
    op.drop_column('s3_dataset', 'deleted')
    op.drop_column('s3_dataset', 'description')
    op.drop_column('s3_dataset', 'environmentUri')
    op.drop_column('s3_dataset', 'organizationUri')
    op.drop_column('s3_dataset', 'region')
    op.drop_column('s3_dataset', 'AwsAccountId')
    op.drop_column('s3_dataset', 'language')
    op.drop_column('s3_dataset', 'topics')
    op.drop_column('s3_dataset', 'confidentiality')
    op.drop_column('s3_dataset', 'tags')
    op.drop_column('s3_dataset', 'businessOwnerEmail')
    op.drop_column('s3_dataset', 'businessOwnerDelegationEmails')
    op.drop_column('s3_dataset', 'stewards')
    op.drop_column('s3_dataset', 'SamlAdminGroupName')
    op.drop_column('s3_dataset', 'autoApprovalEnabled')
    op.drop_column('s3_dataset', 'datasetType')
    op.drop_column('s3_dataset', 'imported')
    # ### end Alembic commands ###


def downgrade():
    Base = declarative_base()

    # Define table classes without polymorphism, as 2 individual entities
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

        datasetType = Column(String, nullable=False)
        imported = Column(Boolean, default=False)

    class S3Dataset(Resource, Base):  # Old S3 Dataset class with all columns
        __tablename__ = 's3_dataset'
        environmentUri = Column(String, nullable=False)  # Foreign key to be added after backfilling
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
        topics = Column(ARRAY(String), nullable=True)
        confidentiality = Column(String, nullable=False, default=ConfidentialityClassification.Unclassified.value)
        tags = Column(ARRAY(String))
        inProject = query_expression()

        bucketCreated = Column(Boolean, default=False)
        glueDatabaseCreated = Column(Boolean, default=False)
        iamAdminRoleCreated = Column(Boolean, default=False)
        iamAdminUserCreated = Column(Boolean, default=False)
        kmsAliasCreated = Column(Boolean, default=False)
        lakeformationLocationCreated = Column(Boolean, default=False)
        bucketPolicyCreated = Column(Boolean, default=False)
        businessOwnerEmail = Column(String, nullable=True)
        businessOwnerDelegationEmails = Column(ARRAY(String), nullable=True)
        stewards = Column(String, nullable=True)

        SamlAdminGroupName = Column(String, nullable=True)

        importedS3Bucket = Column(Boolean, default=False)
        importedGlueDatabase = Column(Boolean, default=False)
        importedKmsKey = Column(Boolean, default=False)
        importedAdminRole = Column(Boolean, default=False)
        imported = Column(Boolean, default=False)

        autoApprovalEnabled = Column(Boolean, default=False)

    # Create columns in s3_dataset table
    op.add_column(
        's3_dataset',
        sa.Column('label', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('name', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('owner', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('created', sa.DateTime(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('updated', sa.DateTime(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('deleted', sa.DateTime(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('description', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('environmentUri', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('organizationUri', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('region', sa.String(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('AwsAccountId', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('language', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('confidentiality', sa.String(), nullable=False, server_default=''),
    )
    op.add_column(
        's3_dataset',
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('businessOwnerEmail', sa.String(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('businessOwnerDelegationEmails', postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('stewards', sa.String(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('SamlAdminGroupName', sa.String(), nullable=True),
    )
    op.add_column(
        's3_dataset',
        sa.Column('autoApprovalEnabled', sa.Boolean(), default=False),
    )
    op.add_column(
        's3_dataset',
        sa.Column(
            'datasetType',
            sa.Enum(DatasetTypes.S3.value, name='datasettypes'),
            nullable=False,
            server_default=DatasetTypes.S3.value,
        ),
    )
    op.add_column(
        's3_dataset',
        sa.Column('imported', sa.Boolean(), default=False),
    )
    # Fill s3_dataset table with data from dataset table
    print('Backfill s3_dataset with dataset data...')
    # Read s3_datasets table rows
    conn = op.get_bind()
    session = orm.Session(bind=conn)
    generic_datasets = {dataset.datasetUri: dataset for dataset in session.query(DatasetBase).all()}
    s3_datasets = session.query(S3Dataset).all()
    for dataset in s3_datasets:
        dataset.label = generic_datasets[dataset.datasetUri].label
        dataset.name = generic_datasets[dataset.datasetUri].name
        dataset.owner = generic_datasets[dataset.datasetUri].owner
        dataset.created = generic_datasets[dataset.datasetUri].created
        dataset.updated = generic_datasets[dataset.datasetUri].updated
        dataset.deleted = generic_datasets[dataset.datasetUri].deleted
        dataset.description = generic_datasets[dataset.datasetUri].description
        dataset.environmentUri = generic_datasets[dataset.datasetUri].environmentUri
        dataset.organizationUri = generic_datasets[dataset.datasetUri].organizationUri
        dataset.region = generic_datasets[dataset.datasetUri].region
        dataset.AwsAccountId = generic_datasets[dataset.datasetUri].AwsAccountId
        dataset.language = generic_datasets[dataset.datasetUri].language
        dataset.topics = generic_datasets[dataset.datasetUri].topics
        dataset.confidentiality = generic_datasets[dataset.datasetUri].confidentiality
        dataset.tags = generic_datasets[dataset.datasetUri].tags
        dataset.businessOwnerEmail = generic_datasets[dataset.datasetUri].businessOwnerEmail
        dataset.businessOwnerDelegationEmails = generic_datasets[dataset.datasetUri].businessOwnerDelegationEmails
        dataset.stewards = generic_datasets[dataset.datasetUri].stewards
        dataset.SamlAdminGroupName = generic_datasets[dataset.datasetUri].SamlAdminGroupName
        dataset.autoApprovalEnabled = generic_datasets[dataset.datasetUri].autoApprovalEnabled
        dataset.datasetType = generic_datasets[dataset.datasetUri].datasetType
        dataset.imported = generic_datasets[dataset.datasetUri].imported
        session.commit()

    # Update foreign keys of dataset_bucket -> to s3_dataset and dataset_lock -> to dataset tables
    op.drop_constraint('dataset_lock_datasetUri_fkey', 'dataset_lock', type_='foreignkey')
    op.create_foreign_key('fk_dataset_lock_datasetUri', 'dataset_lock', 's3_dataset', ['datasetUri'], ['datasetUri'])

    op.drop_constraint('s3_dataset_bucket_datasetUri_fkey', 'dataset_bucket', type_='foreignkey')
    op.create_foreign_key(
        'dataset_bucket_datasetUri_fkey',
        'dataset_bucket',
        's3_dataset',
        ['datasetUri'],
        ['datasetUri'],
        ondelete='CASCADE',
    )

    op.drop_constraint('dataset_environmentUri_fkey', 'dataset', type_='foreignkey')
    op.create_foreign_key(
        's3_dataset_environmentUri_fkey',
        's3_dataset',
        'environment',
        ['environmentUri'],
        ['environmentUri'],
        ondelete='CASCADE',
    )
    # Drop dataset table
    op.drop_constraint('dataset_datasetUri_fkey', 's3_dataset', type_='foreignkey')
    op.drop_table('dataset')

    # ### end Alembic commands ###
