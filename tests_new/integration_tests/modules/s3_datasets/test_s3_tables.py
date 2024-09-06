import logging
import json
import boto3
from assertpy import assert_that
import pytest

from integration_tests.modules.s3_datasets.queries import (
    update_dataset_table,
    delete_table,
    sync_tables,
    create_table_data_filter,
    delete_table_data_filter,
    preview_table,
    get_dataset_table,
    list_dataset_tables,
    generate_dataset_access_token,
)
from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.aws_clients import GlueClient


log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
def test_sync_tables(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    assert_that(len(tables)).is_equal_to(2)
    assert_that(tables[0].label).is_equal_to('integrationtest2')


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_sync_tables_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(sync_tables).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'SYNC_DATASET', dataset_uri
    )


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_dataset_table(client1, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = get_dataset_table(client1, table_uri)
    assert_that(response.label).is_equal_to('integrationtest2')
    assert_that(response.datasetUri).is_equal_to(dataset.datasetUri)


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_list_dataset_tables(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    response = list_dataset_tables(client1, dataset.datasetUri)
    assert_that(response.tables.count).is_equal_to(2)


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
def test_preview_table(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = preview_table(client1, table_uri)
    assert_that(response.rows).exists()


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
def test_preview_table_unauthorized(client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    # TODO: confidentiality levels
    assert_that(preview_table).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'PREVIEW_DATASET_TABLE', table_uri
    )


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
def test_update_dataset_table(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = update_dataset_table(client1, table_uri, input={'label': 'newTableLabel'})
    assert_that(response.label).is_equal_to('newTableLabel')


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_update_dataset_table_unauthorized(client2, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(update_dataset_table).raises(GqlError).when_called_with(
        client2, table_uri, {'label': 'badNewLabel'}
    ).contains('UnauthorizedOperation', 'UPDATE_DATASET_TABLE', dataset.datasetUri)


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_delete_table(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    creds = json.loads(generate_dataset_access_token(client1, dataset.datasetUri))
    dataset_session = boto3.Session(
        aws_access_key_id=creds['AccessKey'],
        aws_secret_access_key=creds['SessionKey'],
        aws_session_token=creds['sessionToken'],
    )
    GlueClient(dataset_session, dataset.region).create_table(
        database_name=dataset.GlueDatabaseName, table_name='todelete', bucket=dataset.S3BucketName
    )
    response = sync_tables(client1, datasetUri=dataset.datasetUri)
    table_uri = [table.tableUri for table in response.get('nodes', []) if table.label == 'todelete'][0]
    response = delete_table(client1, table_uri)
    assert_that(response).is_true()


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
def test_delete_table_unauthorized(client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(delete_table).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'DELETE_DATASET_TABLE', table_uri
    )


def test_create_table_data_filter():
    # TODO
    pass


def test_create_table_data_filter_unauthorized():
    # TODO
    pass


def test_list_table_data_filters():
    # TODO
    pass


def test_list_table_data_filters_unauthorized():
    # TODO
    pass


def test_delete_table_data_filter():
    # TODO
    pass


def test_delete_table_data_filter_unauthorized():
    # TODO
    pass
