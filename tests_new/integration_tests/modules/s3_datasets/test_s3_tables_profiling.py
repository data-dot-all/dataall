import logging
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    delete_table,
    preview_table,
    start_dataset_profiling_run,
    sync_tables,
)
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_start_table_profiling(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    table = tables[0]
    dataset_uri = dataset.datasetUri
    response = start_dataset_profiling_run(
        client1, input={'datasetUri': dataset_uri, 'tableUri': table.tableUri, 'GlueTableName': table.GlueTableName}
    )
    assert_that(response.datasetUri).is_equal_to(dataset_uri)
    assert_that(response.status).is_equal_to('RUNNING')
    assert_that(response.GlueTableName).is_equal_to(table.GlueTableName)


def test_start_table_profiling_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(start_dataset_profiling_run).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'PROFILE_DATASET_TABLE', dataset_uri
    )


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
