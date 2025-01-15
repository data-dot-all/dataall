import logging
import pytest
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    start_dataset_profiling_run,
    list_table_profiling_runs,
    get_table_profiling_run,
)
from integration_tests.errors import GqlError
from integration_tests.utils import poller

log = logging.getLogger(__name__)


def has_job_finished(job):
    return job.status not in ['STARTING', 'RUNNING', 'STOPPING', 'WAITING']


@poller(check_success=has_job_finished, timeout=600)
def check_job_finished(client, table_uri):
    return get_table_profiling_run(client, table_uri)


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [
        pytest.param('session_s3_dataset1', 'session_s3_dataset1_tables', marks=pytest.mark.dependency(name='s1')),
        pytest.param(
            'session_imported_sse_s3_dataset1',
            'session_imported_sse_s3_dataset1_tables',
            marks=pytest.mark.dependency(name='s2'),
        ),
        pytest.param(
            'session_imported_kms_s3_dataset1',
            'session_imported_kms_s3_dataset1_tables',
            marks=pytest.mark.dependency(name='s3'),
        ),
    ],
)
def test_start_table_profiling(client1, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    dataset_uri = dataset.datasetUri
    response = start_dataset_profiling_run(
        client1,
        input={'datasetUri': dataset_uri, 'tableUri': table.tableUri, 'GlueTableName': table.restricted.GlueTableName},
    )
    assert_that(response.datasetUri).is_equal_to(dataset_uri)
    assert_that(response.GlueTableName).is_equal_to(table.restricted.GlueTableName)


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
        pytest.param('session_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['s1'])),
        pytest.param('session_imported_sse_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['s2'])),
        pytest.param('session_imported_kms_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['s3'])),
    ],
)
def test_get_table_profiling_run_succeeded(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    check_job_finished(client1, table.tableUri)
    response = get_table_profiling_run(client1, tableUri=table.tableUri)
    assert_that(response.status).is_equal_to('SUCCEEDED')


@pytest.mark.parametrize(
    'tables_fixture_name,confidentiality',
    [
        pytest.param('session_s3_dataset1_tables', 'Unclassified', marks=pytest.mark.dependency(depends=['s1'])),
        pytest.param(
            'session_imported_sse_s3_dataset1_tables', 'Official', marks=pytest.mark.dependency(depends=['s2'])
        ),
        pytest.param('session_imported_kms_s3_dataset1_tables', 'Secret', marks=pytest.mark.dependency(depends=['s3'])),
    ],
)
def test_get_table_profiling_run_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = get_table_profiling_run(client2, tableUri=table_uri)
        assert_that(response.GlueTableName).is_equal_to(tables[0].restricted.GlueTableName)
    else:
        assert_that(get_table_profiling_run).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'GET_TABLE_PROFILING_METRICS'
        )


@pytest.mark.parametrize(
    'dataset_fixture_name,tables_fixture_name',
    [
        pytest.param('session_s3_dataset1', 'session_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['s1'])),
        pytest.param(
            'session_imported_sse_s3_dataset1',
            'session_imported_sse_s3_dataset1_tables',
            marks=pytest.mark.dependency(depends=['s2']),
        ),
        pytest.param(
            'session_imported_kms_s3_dataset1',
            'session_imported_kms_s3_dataset1_tables',
            marks=pytest.mark.dependency(depends=['s3']),
        ),
    ],
)
def test_list_table_profiling_runs(client1, dataset_fixture_name, tables_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    table = tables[0]
    dataset_uri = dataset.datasetUri
    second_run = start_dataset_profiling_run(
        client1, input={'datasetUri': dataset_uri, 'tableUri': table.tableUri, 'GlueTableName': table.GlueTableName}
    )
    response = list_table_profiling_runs(client1, tableUri=table.tableUri)
    assert_that(response.count).is_equal_to(2)


@pytest.mark.parametrize(
    'tables_fixture_name,confidentiality',
    [
        pytest.param('session_s3_dataset1_tables', 'Unclassified', marks=pytest.mark.dependency(depends=['s1'])),
        pytest.param(
            'session_imported_sse_s3_dataset1_tables', 'Official', marks=pytest.mark.dependency(depends=['s2'])
        ),
        pytest.param('session_imported_kms_s3_dataset1_tables', 'Secret', marks=pytest.mark.dependency(depends=['s3'])),
    ],
)
def test_list_table_profiling_runs_by_confidentiality(client2, tables_fixture_name, confidentiality, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    if confidentiality in ['Unclassified']:
        response = list_table_profiling_runs(client2, tableUri=table_uri)
        assert_that(response.count).is_greater_than_or_equal_to(1)
    else:
        assert_that(list_table_profiling_runs).raises(GqlError).when_called_with(client2, table_uri).contains(
            'UnauthorizedOperation', 'GET_TABLE_PROFILING_METRICS'
        )
