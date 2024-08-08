"""add_backfill_read_folder_permissions

Revision ID: c6d01930179d
Revises: 9dcc2f2b8858
Create Date: 2024-04-11 15:03:35.157904

"""

from alembic import op
from sqlalchemy import orm
from sqlalchemy import and_
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from dataall.base.db import utils, Resource
from datetime import datetime
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_FOLDER_READ, GET_DATASET_FOLDER
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem
from dataall.modules.shares_base.services.shares_enums import ShareItemStatus, ShareableType, ShareObjectStatus
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language

# revision identifiers, used by Alembic.
revision = 'c6d01930179d'
down_revision = '9dcc2f2b8858'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


Base = declarative_base()


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(String, nullable=False, primary_key=True, default=utils.uuid('share'))
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


class Dataset(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, nullable=False)
    organizationUri = Column(String, nullable=False)
    datasetUri = Column(String, primary_key=True, default=utils.uuid('dataset'))
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=False)
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


def attach_dataset_folder_read_permission(session, dataset: Dataset, location_uri):
    """
    Attach Folder permissions to dataset groups
    """
    permission_group = {
        dataset.SamlAdminGroupName,
        dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName,
    }
    for group in permission_group:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group,
            permissions=DATASET_FOLDER_READ,
            resource_uri=location_uri,
            resource_type=DatasetStorageLocation.__name__,
        )


def upgrade():
    session = get_session()

    # Create new folder permission
    folder_permission = PermissionService.save_permission(
        session=session,
        name=GET_DATASET_FOLDER,
        description='GET_DATASET_FOLDER',
        permission_type=PermissionType.RESOURCE.name,
    )

    # Grant folder read permissions to all dataset owners and stewards
    print('Getting all Datasets and granting folder permissions...')
    datasets: [Dataset] = session.query(Dataset).all()
    for dataset in datasets:
        locations: [DatasetStorageLocation] = (
            session.query(DatasetStorageLocation).filter(DatasetStorageLocation.datasetUri == dataset.datasetUri).all()
        )
        for location in locations:
            attach_dataset_folder_read_permission(session, dataset, location.locationUri)

    # Grant folder read permissions to share requesters with active shared folders
    print('Getting all Shares and granting folder permissions...')
    shares: [ShareObject] = session.query(ShareObject).all()
    for share in shares:
        dataset: Dataset = session.query(Dataset).get(share.datasetUri)

        # Attach data.all read permissions to folders
        if dataset and share.groupUri != dataset.SamlAdminGroupName:
            share_folder_items = (
                session.query(ShareObjectItem)
                .filter(
                    (
                        and_(
                            ShareObjectItem.shareUri == share.shareUri,
                            ShareObjectItem.itemType == ShareableType.StorageLocation.value,
                            ShareObjectItem.status.in_(
                                [
                                    ShareItemStatus.Share_Approved.value,
                                    ShareItemStatus.Share_Succeeded.value,
                                    ShareItemStatus.Share_In_Progress.value,
                                ]
                            ),
                        )
                    )
                )
                .all()
            )

            for item in share_folder_items:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=share.groupUri,
                    permissions=DATASET_FOLDER_READ,
                    resource_uri=item.itemUri,
                    resource_type=DatasetStorageLocation.__name__,
                )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    print('Skipping ... ')
    # ### end Alembic commands ###
