import logging

from assertpy import assert_that
import pytest

from integration_tests.modules.s3_datasets.queries import (
    create_table_data_filter,
    delete_table_data_filter,
    list_table_data_filters,
)
from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.global_conftest import COL_FILTER_INPUT
from integration_tests.modules.s3_datasets.conftest import TABLE_FILTERS_FIXTURES_PARAMS, TABLES_FIXTURES_PARAMS

log = logging.getLogger(__name__)


@pytest.mark.parametrize(*TABLE_FILTERS_FIXTURES_PARAMS)
def test_create_table_data_filter(tables_fixture_name, table_filters_fixture_name, request):
    filters = request.getfixturevalue(table_filters_fixture_name)
    tables = request.getfixturevalue(tables_fixture_name)
    assert_that(len(filters)).is_equal_to(4)
    for table in tables:
        table_filters = [f for f in filters if f.tableUri == table.tableUri]
        for f in table_filters:
            assert_that(f.filterType).is_in('ROW', 'COLUMN')
            assert_that(f.filterUri).is_not_none()
            assert_that(f.tableUri).is_equal_to(table.tableUri)


def test_create_table_data_filter_unauthorized(client2, session_s3_dataset1_tables):
    table_uri = session_s3_dataset1_tables[0].tableUri
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, COL_FILTER_INPUT
    ).contains('UnauthorizedOperation', 'CREATE_TABLE_DATA_FILTER', table_uri)


def test_create_table_data_filter_invalid_input(client1, session_s3_dataset1_tables):
    table_uri = session_s3_dataset1_tables[0].tableUri

    # Unknown Filter Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client1, table_uri, input={'filterName': 'columnfilter', 'filterType': 'UNKNOWN', 'includedCols': ['col_0']}
    ).contains('InvalidInput', 'filterType')

    # No Included Cols for COLUMN Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client1, table_uri, input={'filterName': 'columnfilter', 'filterType': 'COLUMN'}
    ).contains('InvalidInput', 'includedCols')

    # No Row Expression for COLUMN Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client1, table_uri, input={'filterName': 'rowfilter', 'filterType': 'ROW'}
    ).contains('InvalidInput', 'rowExpression')

    # No Filter Name
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client1, table_uri, input={'filterType': 'COLUMN', 'includedCols': ['col_0']}
    ).contains('filterName')

    # Bad Filter Name
    filter_name = 'Column !!##$$ Filter'
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client1, table_uri, input={'filterName': filter_name, 'filterType': 'COLUMN'}
    ).contains('InvalidInput', filter_name)


@pytest.mark.parametrize(*TABLES_FIXTURES_PARAMS)
def test_list_table_data_filters(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    for table in tables:
        filters = list_table_data_filters(client1, table.tableUri)
        assert_that(filters.nodes).is_length(2)
        filter_names = [f.label for f in filters.nodes]
        assert_that(filter_names).contains('columnfilter', 'rowfilter')


def test_list_table_data_filters_unauthorized(client2, session_s3_dataset1_tables):
    table_uri = session_s3_dataset1_tables[0].tableUri
    assert_that(list_table_data_filters).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'LIST_TABLE_DATA_FILTERS', table_uri
    )


def test_delete_table_data_filter_unauthorized(client2, session_s3_dataset1_tables_data_filters):
    filter = session_s3_dataset1_tables_data_filters[0]
    assert_that(delete_table_data_filter).raises(GqlError).when_called_with(client2, filter.filterUri).contains(
        'UnauthorizedOperation', 'DELETE_TABLE_DATA_FILTER', filter.tableUri
    )


def test_delete_table_data_filter(client1, session_s3_dataset1_tables):
    table = session_s3_dataset1_tables[0]
    col_filter_input = COL_FILTER_INPUT.copy()
    col_filter_input.update({'filterName': 'todelete'})
    filter = create_table_data_filter(client1, table.tableUri, input=col_filter_input)
    assert_that(delete_table_data_filter(client1, filter.filterUri)).is_true()
