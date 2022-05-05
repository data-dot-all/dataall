import typing

import dataall
import pytest
from dataall.searchproxy import indexers


@pytest.fixture(scope='module', autouse=True)
def org(db):
    with db.scoped_session() as session:
        org = dataall.db.models.Organization(
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
        env = dataall.db.models.Environment(
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
def dataset(org, env, db):
    with db.scoped_session() as session:
        dataset = dataall.db.models.Dataset(
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
            imported=True,
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='module', autouse=True)
def table(org, env, db, dataset):
    with db.scoped_session() as session:
        table = dataall.db.models.DatasetTable(
            datasetUri=dataset.datasetUri,
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


@pytest.fixture(scope='module', autouse=True)
def folder(org, env, db, dataset):
    with db.scoped_session() as session:
        location = dataall.db.models.DatasetStorageLocation(
            datasetUri=dataset.datasetUri,
            AWSAccountId='12345678901',
            S3Prefix='S3prefix',
            label='label',
            owner='foo',
            name='name',
            S3BucketName='S3BucketName',
            region='eu-west-1',
        )
        session.add(location)
    yield location


def test_es_request():
    body = '{"preference":"SearchResult"}\n{"query":{"match_all":{}},"size":8,"_source":{"includes":["*"],"excludes":[]},"from":0}\n'
    body = body.split('\n')
    assert (
        body[1]
        == '{"query":{"match_all":{}},"size":8,"_source":{"includes":["*"],"excludes":[]},"from":0}'
    )
    import json

    assert json.loads(body[1]) == {
        'query': {'match_all': {}},
        'size': 8,
        '_source': {'includes': ['*'], 'excludes': []},
        'from': 0,
    }


def test_upsert_dataset(db, dataset, env, mocker):
    mocker.patch('dataall.searchproxy.upsert', return_value={})
    with db.scoped_session() as session:
        dataset_indexed = indexers.upsert_dataset(
            session, es={}, datasetUri=dataset.datasetUri
        )
        assert dataset_indexed.datasetUri == dataset.datasetUri


def test_upsert_table(db, dataset, env, mocker, table):
    mocker.patch('dataall.searchproxy.upsert', return_value={})
    with db.scoped_session() as session:
        table_indexed = indexers.upsert_table(session, es={}, tableUri=table.tableUri)
        assert table_indexed.uri == table.tableUri


def test_upsert_folder(db, dataset, env, mocker, folder):
    mocker.patch('dataall.searchproxy.upsert', return_value={})
    with db.scoped_session() as session:
        folder_indexed = indexers.upsert_folder(
            session, es={}, locationUri=folder.locationUri
        )
        assert folder_indexed.uri == folder.locationUri


def test_upsert_tables(db, dataset, env, mocker, folder):
    mocker.patch('dataall.searchproxy.upsert', return_value={})
    with db.scoped_session() as session:
        tables = indexers.upsert_dataset_tables(
            session, es={}, datasetUri=dataset.datasetUri
        )
        assert len(tables) == 1
