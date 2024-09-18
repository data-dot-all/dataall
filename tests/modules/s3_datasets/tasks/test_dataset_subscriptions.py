from unittest.mock import MagicMock

import pytest

from dataall.base.db import Engine
from dataall.core.environment.db.environment_models import Environment
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectStatus,
    ShareItemStatus,
    ShareableType,
    PrincipalType,
    ShareObjectDataPermission,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, S3Dataset
from dataall.modules.s3_datasets_shares.tasks.dataset_subscription_task import DatasetSubscriptionService
from dataall.core.environment.api.enums import EnvironmentPermission


@pytest.fixture(scope='module')
def otherenv(org_fixture, db):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org_fixture.organizationUri,
            AwsAccountId='987654321',
            region='eu-west-1',
            label='org',
            owner='bob',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment=EnvironmentPermission.Owner.value,
        )
        session.add(env)
    yield env


@pytest.fixture(scope='module')
def dataset(create_dataset, org_fixture, env_fixture):
    yield create_dataset(org_fixture, env_fixture, 'dataset')


@pytest.fixture(scope='module')
def share(
    dataset: S3Dataset,
    db: Engine,
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
            principalRoleName='uri-group2',
            principalType=PrincipalType.Group.value,
            status=ShareObjectStatus.Approved.value,
            permissions=[ShareObjectDataPermission.Read.value],
        )
        session.add(share)
        session.commit()
        share_item = ShareObjectItem(
            shareUri=share.shareUri,
            owner='alice',
            itemUri=table.tableUri,
            itemType=ShareableType.Table.value,
            itemName=table.GlueTableName,
            status=ShareItemStatus.Share_Approved.value,
        )
        session.add(share_item)


def test_subscriptions(org, env, otherenv, db, dataset, share, mocker):
    sns_client = MagicMock()
    mocker.patch('dataall.modules.s3_datasets_shares.tasks.dataset_subscription_task.SnsDatasetClient', sns_client)
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
