import pytest

from dataall.db import models
from dataall.api import constants
from dataall.modules.dataset_sharing.db.enums import ShareableType, ShareItemStatus, ShareObjectStatus
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset


@pytest.fixture(scope="module")
def group(db):
    with db.scoped_session() as session:
        group = models.Group(name="bobteam", label="bobteam", owner="alice")
        session.add(group)
    yield group


@pytest.fixture(scope="module")
def group2(db):
    with db.scoped_session() as session:
        group = models.Group(name="bobteam2", label="bobteam2", owner="alice2")
        session.add(group)
    yield group


@pytest.fixture(scope="module")
def org(db):
    def factory(label: str, owner: str, SamlGroupName: str) -> models.Organization:
        with db.scoped_session() as session:
            org = models.Organization(
                label=label,
                owner=owner,
                tags=[],
                description="desc",
                SamlGroupName=SamlGroupName,
            )
            session.add(org)
            session.commit()
            return org

    yield factory


@pytest.fixture(scope="module")
def environment(db):
    def factory(
        organization: models.Organization,
        awsAccountId: str,
        label: str,
        owner: str,
        samlGroupName: str,
        environmentDefaultIAMRoleName: str,
        dashboardsEnabled: bool = False,
    ) -> models.Environment:
        with db.scoped_session() as session:
            env = models.Environment(
                organizationUri=organization.organizationUri,
                AwsAccountId=awsAccountId,
                region="eu-central-1",
                label=label,
                owner=owner,
                tags=[],
                description="desc",
                SamlGroupName=samlGroupName,
                EnvironmentDefaultIAMRoleName=environmentDefaultIAMRoleName,
                EnvironmentDefaultIAMRoleArn=f"arn:aws:iam::{awsAccountId}:role/{environmentDefaultIAMRoleName}",
                CDKRoleArn=f"arn:aws::{awsAccountId}:role/EnvRole",
                dashboardsEnabled=dashboardsEnabled,
            )
            session.add(env)
            session.commit()
        return env

    yield factory


@pytest.fixture(scope="module")
def environment_group(db):
    def factory(
        environment: models.Environment,
        group: models.Group,
    ) -> models.EnvironmentGroup:
        with db.scoped_session() as session:

            env_group = models.EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group.groupUri,
                environmentIAMRoleArn=environment.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=environment.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup="workgroup",
            )
            session.add(env_group)
            session.commit()
            return env_group

    yield factory


@pytest.fixture(scope="module")
def dataset(db):
    def factory(
        organization: models.Organization,
        environment: models.Environment,
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
        environment: models.Environment,
        env_group: models.EnvironmentGroup
    ) -> ShareObject:
        with db.scoped_session() as session:
            share = ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner="bob",
                principalId=environment.SamlGroupName,
                principalType=constants.PrincipalType.Group.value,
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
