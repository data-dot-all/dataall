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


def test_sync_dataset_table_columns():
    # TODO
    pass


def test_sync_dataset_table_columns_unauthorized():
    # TODO
    pass


def test_update_dataset_table_column():
    # TODO
    pass


def test_update_dataset_table_column_unauthorized():
    # TODO
    pass


def test_list_dataset_table_columns():
    # TODO
    pass


def test_list_dataset_table_columns_unauthorized():
    # TODO
    pass
