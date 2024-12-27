import logging
import json
import boto3
from assertpy import assert_that
import pytest

from integration_tests.modules.s3_datasets.queries import (
    update_dataset_table,
    delete_table,
    sync_tables,
    preview_table,
    get_dataset_table,
    list_dataset_tables,
    generate_dataset_access_token,
)
from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.aws_clients import GlueClient
from integration_tests.modules.s3_datasets.conftest import (
    TABLES_FIXTURES_PARAMS,
    DATASETS_FIXTURES_PARAMS,
    DATASETS_TABLES_FIXTURES_PARAMS,
    TABLES_CONFIDENTIALITY_FIXTURES_PARAMS,
)

log = logging.getLogger(__name__)


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_sync_tables(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    assert_that(len(tables)).is_equal_to(2)
    assert_that(tables[0].label).is_equal_to('integrationtest2')


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1'],
)
def test_sync_tables_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(sync_tables).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'SYNC_DATASET', dataset_uri
    )


@pytest.mark.parametrize(*DATASETS_TABLES_FIXTURES_PARAMS)
def test_get_dataset_table(client1, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = get_dataset_table(client1, table_uri)
    assert_that(response.label).is_equal_to('integrationtest2')
    assert_that(response.datasetUri).is_equal_to(dataset.datasetUri)


@pytest.mark.parametrize(*DATASETS_FIXTURES_PARAMS)
def test_list_dataset_tables(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    response = list_dataset_tables(client1, dataset.datasetUri)
    assert_that(response.tables.count).is_greater_than_or_equal_to(2)
    tables = [
        table
        for table in response.tables.get('nodes', [])
        if table.restricted.GlueTableName.startswith('integrationtest')
    ]
    assert_that(len(tables)).is_equal_to(2)


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_preview_table(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = preview_table(client1, table_uri)
    assert_that(len(response.rows)).is_equal_to(3)
    assert_that(response.rows[0]).contains('value12', 'value13')


@pytest.mark.parametrize(*TABLES_CONFIDENTIALITY_FIXTURES_PARAMS)
def test_preview_table_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = preview_table(client2, table_uri)
        assert_that(len(response.rows)).is_equal_to(3)
        assert_that(response.rows[0]).contains('value12', 'value13')
    else:
        assert_that(preview_table).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'PREVIEW_DATASET_TABLE'
        )


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_update_dataset_table(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = update_dataset_table(client1, table_uri, input={'label': 'newTableLabel'})
    assert_that(response.label).is_equal_to('newTableLabel')


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [('session_s3_dataset1', 'session_s3_dataset1_tables')],
)
def test_update_dataset_table_unauthorized(client2, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(update_dataset_table).raises(GqlError).when_called_with(
        client2, table_uri, {'label': 'badNewLabel'}
    ).contains('UnauthorizedOperation', 'UPDATE_DATASET_TABLE', dataset.datasetUri)


@pytest.mark.parametrize(*DATASETS_FIXTURES_PARAMS)
def test_delete_table(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    creds = json.loads(generate_dataset_access_token(client1, dataset.datasetUri))
    dataset_session = boto3.Session(
        aws_access_key_id=creds['AccessKey'],
        aws_secret_access_key=creds['SessionKey'],
        aws_session_token=creds['sessionToken'],
    )
    GlueClient(dataset_session, dataset.restricted.region).create_table(
        database_name=dataset.restricted.GlueDatabaseName, table_name='todelete', bucket=dataset.restricted.S3BucketName
    )
    sync_tables(client1, datasetUri=dataset.datasetUri)
    response = list_dataset_tables(client1, datasetUri=dataset.datasetUri)
    table_uri = [table.tableUri for table in response.tables.get('nodes', []) if table.label == 'todelete'][0]
    response = delete_table(client1, table_uri)
    assert_that(response).is_true()


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [('session_s3_dataset1', 'session_s3_dataset1_tables')],
)
def test_delete_table_unauthorized(client2, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(delete_table).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'DELETE_DATASET_TABLE', dataset.datasetUri
    )
