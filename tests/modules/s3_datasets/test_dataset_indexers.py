from dataall.modules.s3_datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.s3_datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer


def test_es_request():
    body = '{"preference":"SearchResult"}\n{"query":{"match_all":{}},"size":8,"_source":{"includes":["*"],"excludes":[]},"from":0}\n'
    body = body.split('\n')
    assert body[1] == '{"query":{"match_all":{}},"size":8,"_source":{"includes":["*"],"excludes":[]},"from":0}'
    import json

    assert json.loads(body[1]) == {
        'query': {'match_all': {}},
        'size': 8,
        '_source': {'includes': ['*'], 'excludes': []},
        'from': 0,
    }


def test_upsert_dataset(db, dataset_fixture, env):
    with db.scoped_session() as session:
        dataset_indexed = DatasetIndexer.upsert(session, dataset_uri=dataset_fixture.datasetUri)
        assert dataset_indexed.datasetUri == dataset_fixture.datasetUri


def test_upsert_table(db, dataset_fixture, table_fixture):
    with db.scoped_session() as session:
        table_indexed = DatasetTableIndexer.upsert(session, table_uri=table_fixture.tableUri)
        assert table_indexed.tableUri == table_fixture.tableUri


def test_upsert_folder(db, dataset_fixture, folder_fixture):
    with db.scoped_session() as session:
        folder_indexed = DatasetLocationIndexer.upsert(session=session, folder_uri=folder_fixture.locationUri)
        assert folder_indexed.locationUri == folder_fixture.locationUri


def test_upsert_tables(db, dataset_fixture, folder_fixture):
    with db.scoped_session() as session:
        tables = DatasetTableIndexer.upsert_all(session, dataset_uri=dataset_fixture.datasetUri)
        assert len(tables) == 1
