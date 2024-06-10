from unittest.mock import MagicMock

import pytest
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable
from dataall.modules.s3_datasets.tasks.tables_syncer import sync_tables


@pytest.fixture(scope='module', autouse=True)
def sync_dataset(create_dataset, org_fixture, env_fixture, db):
    yield create_dataset(org_fixture, env_fixture, 'dataset')


@pytest.fixture(scope='module', autouse=True)
def table_fixture(org, env, db, sync_dataset):
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


def test_tables_sync(db, org, env, sync_dataset, table_fixture, mocker):
    mock_crawler = MagicMock()
    mocker.patch('dataall.modules.s3_datasets.tasks.tables_syncer.DatasetCrawler', mock_crawler)
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )

    mock_crawler().list_glue_database_tables.return_value = [
        {
            'Name': 'new_table',
            'DatabaseName': sync_dataset.GlueDatabaseName,
            'StorageDescriptor': {
                'Columns': [
                    {
                        'Name': 'col1',
                        'Type': 'string',
                        'Comment': 'comment_col',
                        'Parameters': {'colp1': 'p1'},
                    },
                ],
                'Location': f's3://{sync_dataset.S3BucketName}/table1',
                'Parameters': {'p1': 'p1'},
            },
            'PartitionKeys': [
                {
                    'Name': 'partition1',
                    'Type': 'string',
                    'Comment': 'comment_partition',
                    'Parameters': {'partition_1': 'p1'},
                },
            ],
        },
        {
            'Name': 'table1',
            'DatabaseName': sync_dataset.GlueDatabaseName,
            'StorageDescriptor': {
                'Columns': [
                    {
                        'Name': 'col1',
                        'Type': 'string',
                        'Comment': 'comment_col',
                        'Parameters': {'colp1': 'p1'},
                    },
                ],
                'Location': f's3://{sync_dataset.S3BucketName}/table1',
                'Parameters': {'p1': 'p1'},
            },
            'PartitionKeys': [
                {
                    'Name': 'partition1',
                    'Type': 'string',
                    'Comment': 'comment_partition',
                    'Parameters': {'partition_1': 'p1'},
                },
            ],
        },
    ]

    mocker.patch('dataall.modules.s3_datasets.tasks.tables_syncer.is_assumable_pivot_role', return_value=True)

    mock_client = MagicMock()
    mocker.patch('dataall.modules.s3_datasets.tasks.tables_syncer.LakeFormationTableClient', mock_client)
    mock_client.grant_principals_all_table_permissions = True

    processed_tables = sync_tables(engine=db)
    assert len(processed_tables) == 2
    with db.scoped_session() as session:
        saved_table: DatasetTable = session.query(DatasetTable).filter(DatasetTable.GlueTableName == 'table1').first()
        assert saved_table
        assert saved_table.GlueTableName == 'table1'
