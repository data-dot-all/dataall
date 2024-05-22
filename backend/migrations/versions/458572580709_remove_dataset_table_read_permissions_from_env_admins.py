"""remove_dataset_table_read_permissions_from_env_admins

Revision ID: 458572580709
Revises: c6d01930179d
Create Date: 2024-05-01 17:14:08.190904

"""

from alembic import op
from sqlalchemy import and_
from sqlalchemy import orm, Column, String, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils, Resource

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService

from dataall.modules.s3_datasets.db.dataset_models import DatasetTable
from dataall.modules.shares_base.db.share_object_models import ShareObject, ShareObjectItem
from dataall.modules.shares_base.services.shares_enums import ShareItemStatus, ShareableType, PrincipalType
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language

# revision identifiers, used by Alembic.
revision = '458572580709'
down_revision = 'a991ac7a85a2'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


Base = declarative_base()


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


def upgrade():
    session = get_session()

    datasets: [Dataset] = session.query(Dataset).all()
    for dataset in datasets:
        environment = EnvironmentService.get_environment_by_uri(session, uri=dataset.environmentUri)
        env_admin_group = environment.SamlGroupName

        # if envAdmis is also Dataset admin, no need to delete permissions
        if env_admin_group == dataset.SamlAdminGroupName or env_admin_group == dataset.stewards:
            continue

        tables: [DatasetTable] = session.query(DatasetTable).filter(DatasetTable.datasetUri == dataset.datasetUri).all()
        for table in tables:
            # check, if table was shared with  env_admin_group
            table_was_shared = session.query(
                session.query(ShareObjectItem)
                .join(
                    ShareObject,
                    ShareObject.shareUri == ShareObjectItem.shareItemUri,
                )
                .filter(
                    (
                        and_(
                            ShareObject.principalType == PrincipalType.Group.value,
                            ShareObject.principalId == env_admin_group,
                            ShareObjectItem.shareItemUri == table.tableUri,
                            ShareObjectItem.itemType == ShareableType.Table.value,
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
                .exists()
            ).scalar()

            if not table_was_shared:
                print(
                    f'Table with uri = {table.tableUri} was not shared with group {env_admin_group}. Remove '
                    f'resource policy.'
                )
                ResourcePolicyService.delete_resource_policy(
                    session, env_admin_group, table.tableUri, DatasetTable.__name__
                )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    print('Skipping ... ')
    # ### end Alembic commands ###
