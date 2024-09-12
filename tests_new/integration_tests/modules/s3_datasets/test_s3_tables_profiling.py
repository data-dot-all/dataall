import logging
import pytest
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    start_dataset_profiling_run,
    list_table_profiling_runs,
    get_table_profiling_run,
)
from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.conftest import DATASETS_TABLES_FIXTURES_PARAMS

log = logging.getLogger(__name__)


@pytest.mark.parametrize(*DATASETS_TABLES_FIXTURES_PARAMS)
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


def test_list_table_profiling_runs():
    # TODO
    pass


def test_list_table_profiling_runs_unauthorized():
    # TODO
    pass


def test_get_table_profiling_run():
    # TODO
    pass


def test_get_table_profiling_run_unauthorized():
    # TODO
    pass
