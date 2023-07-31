import pytest

import dataall
from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset


@pytest.fixture(scope='module', autouse=True)
def org(db):
    with db.scoped_session() as session:
        org = Organization(
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            userRoleInOrganization='Owner',
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module', autouse=True)
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


@pytest.fixture(scope='module', autouse=True)
def sync_dataset(org, env, db):
    with db.scoped_session() as session:
        dataset = Dataset(
            organizationUri=org.organizationUri,
            environmentUri=env.environmentUri,
            label='label',
            owner='foo',
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


@pytest.fixture(scope='module', autouse=True)
def table(org, env, db, sync_dataset):
    with db.scoped_session() as session:
        table = DatasetTable(
            datasetUri=sync_dataset.datasetUri,
            AWSAccountId='12345678901',
            S3Prefix='S3prefix',
            label='label',
            owner='foo',
            name='name',
            GlueTableName='table1',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            region='eu-west-1',
        )
        session.add(table)
    yield table


def test_catalog_indexer(db, org, env, sync_dataset, table, mocker):
    mocker.patch(
        'dataall.modules.datasets.indexers.table_indexer.DatasetTableIndexer.upsert_all',
        return_value=[table]
    )
    mocker.patch(
        'dataall.modules.datasets.indexers.dataset_indexer.DatasetIndexer.upsert', return_value=sync_dataset
    )
    indexed_objects_counter = dataall.core.catalog.tasks.catalog_indexer_task.index_objects(
        engine=db
    )
    assert indexed_objects_counter == 2
