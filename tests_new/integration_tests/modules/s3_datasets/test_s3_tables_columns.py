import logging
import pytest
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    sync_dataset_table_columns,
    update_dataset_table_column,
    list_dataset_table_columns,
)
from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.conftest import (
    TABLES_FIXTURES_PARAMS,
    TABLES_CONFIDENTIALITY_FIXTURES_PARAMS,
)

log = logging.getLogger(__name__)


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_sync_dataset_table_columns(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    response = sync_dataset_table_columns(client1, tables[0].tableUri)
    assert_that(response.count).is_equal_to(3)
    assert_that(response.nodes[0].name).is_equal_to('column1')
    assert_that(response.nodes[0].typeName).is_equal_to('int')


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [('session_s3_dataset1', 'session_s3_dataset1_tables')],
)
def test_sync_dataset_table_columns_unauthorized(client2, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(sync_dataset_table_columns).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'UPDATE_DATASET_TABLE', dataset.datasetUri
    )


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_list_dataset_table_columns(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = list_dataset_table_columns(client1, table_uri)
    assert_that(response.count).is_equal_to(3)
    assert_that(response.nodes[0].name).is_equal_to('column1')
    assert_that(response.nodes[0].columnUri).is_not_none()


@pytest.mark.parametrize(*TABLES_CONFIDENTIALITY_FIXTURES_PARAMS)
def test_list_dataset_table_columns_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = list_dataset_table_columns(client2, table_uri)
        assert_that(response.count).is_equal_to(3)
    else:
        assert_that(list_dataset_table_columns).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'LIST_DATASET_TABLE_COLUMNS'
        )


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_update_dataset_table_column(client1, tables_fixture_name, request, session_id):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    columns = list_dataset_table_columns(client1, table_uri)
    column_uri = columns.nodes[0].columnUri
    response = update_dataset_table_column(
        client1, column_uri, {'description': f'{session_id} new updated description'}
    )
    assert_that(response.description).is_equal_to(f'{session_id} new updated description')


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [('session_s3_dataset1', 'session_s3_dataset1_tables')],
)
def test_update_dataset_table_column_unauthorized(client1, client2, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    columns = list_dataset_table_columns(client1, table_uri)
    column_uri = columns.nodes[0].columnUri
    assert_that(update_dataset_table_column).raises(GqlError).when_called_with(
        client2, column_uri, {'description': 'badNewDescription'}
    ).contains('UnauthorizedOperation', 'UPDATE_DATASET_TABLE', dataset.datasetUri)
