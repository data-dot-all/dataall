import logging
import pytest
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    start_dataset_profiling_run,
    list_table_profiling_runs,
    get_table_profiling_run,
)
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [
        ('session_s3_dataset1', 'session_s3_dataset1_tables'),
        ('session_imported_sse_s3_dataset1', 'session_imported_sse_s3_dataset1_tables'),
        ('session_imported_kms_s3_dataset1', 'session_imported_kms_s3_dataset1_tables'),
    ],
)
def test_start_table_profiling(client1, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    dataset_uri = dataset.datasetUri
    response = start_dataset_profiling_run(
        client1, input={'datasetUri': dataset_uri, 'tableUri': table.tableUri, 'GlueTableName': table.GlueTableName}
    )
    assert_that(response.datasetUri).is_equal_to(dataset_uri)
    assert_that(response.status).is_equal_to('RUNNING')
    assert_that(response.GlueTableName).is_equal_to(table.GlueTableName)


@pytest.mark.parametrize('dataset_fixture_name', ['session_s3_dataset1'])
def test_start_table_profiling_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(start_dataset_profiling_run).raises(GqlError).when_called_with(
        client2, input={'datasetUri': dataset_uri}
    ).contains('UnauthorizedOperation', 'PROFILE_DATASET_TABLE', dataset_uri)


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
@pytest.mark.dependency(depends=['test_start_table_profiling'])
def test_list_table_profiling_runs(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    response = list_table_profiling_runs(client1, tableUri=table.tableUri)
    assert_that(response.count).is_equal_to(1)
    assert_that(response.nodes[0].status).is_in(['STARTING', 'RUNNING', 'SUCCEEDED'])


@pytest.mark.parametrize(
    'tables_fixture_name, confidentiality',
    [
        ('session_s3_dataset1_tables', 'Unclassified'),
        ('session_imported_sse_s3_dataset1_tables', 'Official'),
        ('session_imported_kms_s3_dataset1_tables', 'Secret'),
    ],
)
@pytest.mark.dependency(depends=['test_start_table_profiling'])
def test_list_table_profiling_runs_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = list_table_profiling_runs(client2, tableUri=table_uri)
        assert_that(response.count).is_equal_to(1)
    else:
        assert_that(list_table_profiling_runs).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'GET_TABLE_PROFILING_METRICS'
        )


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)
@pytest.mark.dependency(depends=['test_start_table_profiling'])
def test_get_table_profiling_run(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    response = get_table_profiling_run(client1, tableUri=table.tableUri)
    assert_that(response.status).is_in(['STARTING', 'RUNNING', 'SUCCEEDED'])


@pytest.mark.parametrize(
    'tables_fixture_name, confidentiality',
    [
        ('session_s3_dataset1_tables', 'Unclassified'),
        ('session_imported_sse_s3_dataset1_tables', 'Official'),
        ('session_imported_kms_s3_dataset1_tables', 'Secret'),
    ],
)
@pytest.mark.dependency(depends=['test_start_table_profiling'])
def test_get_table_profiling_run_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = get_table_profiling_run(client2, tableUri=table_uri)
        assert_that(response.count).is_equal_to(1)
    else:
        assert_that(get_table_profiling_run).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'GET_TABLE_PROFILING_METRICS'
        )
