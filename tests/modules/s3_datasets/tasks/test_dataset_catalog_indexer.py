import pytest

from dataall.modules.catalog.tasks.catalog_indexer_task import CatalogIndexerTask
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, S3Dataset


@pytest.fixture(scope='module', autouse=True)
def sync_dataset(org_fixture, env_fixture, db):
    with db.scoped_session() as session:
        dataset = S3Dataset(
            organizationUri=org_fixture.organizationUri,
            environmentUri=env_fixture.environmentUri,
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
        'dataall.modules.s3_datasets.indexers.table_indexer.DatasetTableIndexer.upsert_all', return_value=[table]
    )
    mocker.patch(
        'dataall.modules.s3_datasets.indexers.dataset_indexer.DatasetIndexer.upsert', return_value=sync_dataset
    )
    indexed_objects_counter = CatalogIndexerTask.index_objects(engine=db)
    # Count should be One table + One Dataset = 2
    assert indexed_objects_counter == 2


def test_catalog_indexer_with_deletes(db, org, env, sync_dataset, table, mocker):
    # When Table no longer exists
    mocker.patch('dataall.modules.s3_datasets.indexers.table_indexer.DatasetTableIndexer.upsert_all', return_value=[])
    mocker.patch(
        'dataall.modules.s3_datasets.indexers.dataset_indexer.DatasetIndexer.upsert', return_value=sync_dataset
    )
    mocker.patch(
        'dataall.modules.catalog.indexers.base_indexer.BaseIndexer.search_all',
        return_value=[{'_id': table.tableUri}],
    )
    delete_doc_path = mocker.patch(
        'dataall.modules.catalog.indexers.base_indexer.BaseIndexer.delete_doc', return_value=True
    )

    # And with_deletes 'True' for index_objects
    indexed_objects_counter = CatalogIndexerTask.index_objects(engine=db, with_deletes='True')

    # Index Objects Should call Delete Doc 1 time for Table
    assert delete_doc_path.call_count == 1

    # Count should be One Dataset = 1
    assert indexed_objects_counter == 1
