import logging
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import (
    delete_table,
    preview_table,
    sync_tables,
)
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_update_dataset_table():
    # TODO
    pass


def test_update_dataset_table_unauthorized():
    # TODO
    pass


def test_delete_table(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    table_uri = tables[0].tableUri
    response = delete_table(client1, table_uri)
    assert_that(response).is_true()


def test_delete_table_unauthorized(client2, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    table_uri = tables[0].tableUri
    assert_that(delete_table).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'DELETE_DATASET_TABLE', table_uri
    )


def test_sync_tables(client1, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    response = sync_tables(client1, datasetUri=dataset_uri)
    assert_that(response.count).is_equal_to(2)


def test_sync_tables_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(sync_tables).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'SYNC_DATASET', dataset_uri
    )


def test_create_table_data_filter():
    # TODO
    pass


def test_create_table_data_filter_unauthorized():
    # TODO
    pass


def test_delete_table_data_filter():
    # TODO
    pass


def test_delete_table_data_filter_unauthorized():
    # TODO
    pass


def test_get_dataset_table():
    # TODO
    pass


def test_get_dataset_table_unauthorized():
    # TODO
    pass


def test_list_dataset_tables():
    # TODO
    pass


def test_list_dataset_tables_unauthorized():
    # TODO
    pass


def test_preview_table(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    table_uri = tables[0].tableUri
    response = preview_table(client1, table_uri)
    assert_that(response.rows).exists()


def test_preview_table_unauthorized(client2, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    table_uri = tables[0].tableUri
    # TODO: confidentiality levels
    assert_that(preview_table).raises(GqlError).when_called_with(client2, table_uri, {}).contains(
        'UnauthorizedOperation', 'PREVIEW_DATASET_TABLE', table_uri
    )


def test_list_table_data_filters():
    # TODO
    pass


def test_list_table_data_filters_unauthorized():
    # TODO
    pass
