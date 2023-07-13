from unittest.mock import MagicMock

import pytest

import dataall
from dataall.api.constants import OrganisationUserRole
from dataall.core.environment.db.models import Environment
from dataall.modules.dataset_sharing.db.enums import ShareObjectStatus, ShareItemStatus, ShareableType
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.modules.datasets.tasks.dataset_subscription_task import DatasetSubscriptionService


@pytest.fixture(scope='module')
def org(db):
    with db.scoped_session() as session:
        org = dataall.db.models.Organization(
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module')
def env(org, db):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org.organizationUri,
            AwsAccountId='12345678901',
            region='eu-west-1',
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment='999',
        )
        session.add(env)
    yield env


@pytest.fixture(scope='module')
def otherenv(org, db):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org.organizationUri,
            AwsAccountId='987654321',
            region='eu-west-1',
            label='org',
            owner='bob',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment='999',
        )
        session.add(env)
    yield env


@pytest.fixture(scope='module')
def dataset(org, env, db):
    with db.scoped_session() as session:
        dataset = Dataset(
            organizationUri=org.organizationUri,
            environmentUri=env.environmentUri,
            label='label',
            owner='alice',
            SamlAdminGroupName='foo',
            businessOwnerDelegationEmails=['foo@amazon.com'],
            businessOwnerEmail=['bar@amazon.com'],
            name='name',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            KmsAlias='kmsalias',
            AwsAccountId='123456789012',
            region='eu-west-1',
            IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
            IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='module')
def share(
    dataset: Dataset,
    db: dataall.db.Engine,
    otherenv: Environment,
):
    with db.scoped_session() as session:

        table = DatasetTable(
            label='foo',
            name='foo',
            owner='alice',
            description='test table',
            tags=['a', 'b'],
            datasetUri=dataset.datasetUri,
            tableUri='foo',
            S3Prefix='s3://dataset/testtable/csv/',
            GlueDatabaseName=dataset.GlueDatabaseName,
            GlueTableName='foo',
            S3BucketName=dataset.S3BucketName,
            AWSAccountId=dataset.AwsAccountId,
            region=dataset.region,
        )
        session.add(table)
        share = ShareObject(
            datasetUri=dataset.datasetUri,
            environmentUri=otherenv.environmentUri,
            owner='bob',
            principalId='group2',
            principalType=dataall.api.constants.PrincipalType.Environment.value,
            status=ShareObjectStatus.Approved.value,
        )
        session.add(share)
        session.commit()
        share_item = ShareObjectItem(
            shareUri=share.shareUri,
            owner='alice',
            itemUri=table.tableUri,
            itemType=ShareableType.Table.value,
            itemName=table.GlueTableName,
            GlueDatabaseName=table.GlueDatabaseName,
            GlueTableName=table.GlueTableName,
            status=ShareItemStatus.Share_Approved.value,
        )
        session.add(share_item)


def test_subscriptions(org, env, otherenv, db, dataset, share, mocker):
    sns_client = MagicMock()
    mocker.patch(
        'dataall.modules.datasets.tasks.dataset_subscription_task.SnsDatasetClient',
        sns_client
    )
    sns_client.publish_dataset_message.return_value = True
    subscriber = DatasetSubscriptionService(db)
    messages = [
        {
            'prefix': 's3://dataset/testtable/csv/',
            'accountid': '123456789012',
            'region': 'eu-west-1',
        }
    ]
    envs = subscriber.get_environments(db)
    assert envs
    queues = subscriber.get_queues(envs)
    assert queues
    assert subscriber.notify_consumers(db, messages)
