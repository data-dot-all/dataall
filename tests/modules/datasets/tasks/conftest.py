import pytest

from dataall.core.cognito_groups.db.cognito_group_models import Group
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.db.enums import ShareableType, ShareItemStatus, ShareObjectStatus, PrincipalType
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset


@pytest.fixture(scope="module")
def create_dataset(db):
    def factory(
        organization: Organization,
        environment: Environment,
        label: str,
    ) -> Dataset:
        with db.scoped_session() as session:
            dataset = Dataset(
                organizationUri=organization.organizationUri,
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                SamlAdminGroupName=environment.SamlGroupName,
                businessOwnerDelegationEmails=["foo@amazon.com"],
                name=label,
                S3BucketName=label,
                GlueDatabaseName="gluedatabase",
                KmsAlias="kmsalias",
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                IAMDatasetAdminUserArn=f"arn:aws:iam::{environment.AwsAccountId}:user/dataset",
                IAMDatasetAdminRoleArn=f"arn:aws:iam::{environment.AwsAccountId}:role/dataset",
            )
            session.add(dataset)
            session.commit()
            return dataset

    yield factory


@pytest.fixture(scope="module")
def location(db):
    def factory(dataset: Dataset, label: str) -> DatasetStorageLocation:

        with db.scoped_session() as session:
            ds_location = DatasetStorageLocation(
                name=label,
                label=label,
                owner=dataset.owner,
                datasetUri=dataset.datasetUri,
                S3BucketName=dataset.S3BucketName,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3Prefix=f"{label}",
            )
            session.add(ds_location)
        return ds_location

    yield factory


@pytest.fixture(scope='module')
def table(db):
    def factory(dataset: Dataset, label: str) -> DatasetTable:

        with db.scoped_session() as session:
            table = DatasetTable(
                name=label,
                label=label,
                owner=dataset.owner,
                datasetUri=dataset.datasetUri,
                GlueDatabaseName=dataset.GlueDatabaseName,
                GlueTableName=label,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3BucketName=dataset.S3BucketName,
                S3Prefix=f'{label}',
            )
            session.add(table)
        return table

    yield factory


@pytest.fixture(scope="module")
def share(db):
    def factory(
        dataset: Dataset,
        environment: Environment,
        env_group: EnvironmentGroup
    ) -> ShareObject:
        with db.scoped_session() as session:
            share = ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner="bob",
                principalId=environment.SamlGroupName,
                principalType=PrincipalType.Group.value,
                principalIAMRoleName=env_group.environmentIAMRoleName,
                status=ShareObjectStatus.Approved.value,
            )
            session.add(share)
            session.commit()
            return share

    yield factory


@pytest.fixture(scope="module")
def share_item_folder(db):
    def factory(
        share: ShareObject,
        location: DatasetStorageLocation,
    ) -> ShareObjectItem:
        with db.scoped_session() as session:
            share_item = ShareObjectItem(
                shareUri=share.shareUri,
                owner="alice",
                itemUri=location.locationUri,
                itemType=ShareableType.StorageLocation.value,
                itemName=location.name,
                status=ShareItemStatus.Share_Approved.value,
            )
            session.add(share_item)
            session.commit()
            return share_item

    yield factory


@pytest.fixture(scope="module")
def share_item_table(db):
    def factory(
        share: ShareObject,
        table: DatasetTable,
        status: str,
    ) -> ShareObjectItem:
        with db.scoped_session() as session:
            share_item = ShareObjectItem(
                shareUri=share.shareUri,
                owner="alice",
                itemUri=table.tableUri,
                itemType=ShareableType.Table.value,
                itemName=table.name,
                status=status,
            )
            session.add(share_item)
            session.commit()
            return share_item

    yield factory
