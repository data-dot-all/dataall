import logging

from assertpy import assert_that
import pytest

from integration_tests.modules.s3_datasets.queries import (
    create_table_data_filter,
    delete_table_data_filter,
    list_table_data_filters,
)
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)

COL_INPUT = {
    'filterName': 'columnfilter',
    'description': 'test column',
    'filterType': 'COLUMN',
    'includedCols': ['col_0'],
}
ROW_INPUT = {
    'filterName': 'rowfilter',
    'description': 'test row',
    'filterType': 'ROW',
    'rowExpression': 'col_1 LIKE "%value%" AND col_0 IS NOT NULL',
}


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        pytest.param('session_s3_dataset1_tables', marks=pytest.mark.dependency(name='f1')),
        pytest.param(
            'session_imported_sse_s3_dataset1_tables',
            marks=pytest.mark.dependency(name='f2'),
        ),
        pytest.param(
            'session_imported_kms_s3_dataset1_tables',
            marks=pytest.mark.dependency(name='f3'),
        ),
    ],
)
def test_create_table_data_filter(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    response = create_table_data_filter(client1, table_uri, 'test', COL_INPUT)
    assert_that(response.tableUri).is_equal_to(table_uri)
    assert_that(response.includedCols).is_equal_to(COL_INPUT['includedCols'])
    assert_that(response.filterUri).is_not_none()

    response = create_table_data_filter(client1, table_uri, 'test', ROW_INPUT)
    assert_that(response.tableUri).is_equal_to(table_uri)
    assert_that(response.rowExpression).is_equal_to(ROW_INPUT['rowExpression'])
    assert_that(response.filterUri).is_not_none()


@pytest.mark.parametrize('tables_fixture_name', ['session_s3_dataset1_tables'])
def test_create_table_data_filter_unauthorized(client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri

    assert_that(create_table_data_filter).raises(GqlError).when_called_with(client2, table_uri, COL_INPUT).contains(
        'UnauthorizedOperation', 'CREATE_TABLE_DATA_FILTER', table_uri
    )


@pytest.mark.parametrize('tables_fixture_name', ['session_s3_dataset1_tables'])
def test_create_table_data_filter_invalid_input(client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri

    # Unknown Filter Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, input={'filterName': 'columnfilter', 'filterType': 'UNKNOWN', 'includedCols': ['col_0']}
    ).contains('InvalidInput', 'filterType')

    # No Included Cols for COLUMN Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, input={'filterName': 'columnfilter', 'filterType': 'COLUMN'}
    ).contains('InvalidInput', 'includedCols')

    # No Row Expression for COLUMN Type
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, input={'filterName': 'rowfilter', 'filterType': 'ROW'}
    ).contains('InvalidInput', 'rowExpression')

    # No Filter Name
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, input={'filterType': 'COLUMN', 'includedCols': ['col_0']}
    ).contains('RequiredParameter', 'filterName')

    # Bad Filter Name
    filter_name = 'Column !!##$$ Filter'
    assert_that(create_table_data_filter).raises(GqlError).when_called_with(
        client2, table_uri, input={'filterName': filter_name, 'filterType': 'COLUMN'}
    ).contains('InvalidInput', filter_name)


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        pytest.param('session_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f1'])),
        pytest.param('session_imported_sse_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f2'])),
        pytest.param('session_imported_kms_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f3'])),
    ],
)
def test_list_table_data_filters(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    filters = list_table_data_filters(client1, table_uri)
    assert_that(filters.nodes).is_length(2)
    filter_names = [f.filterName for f in filters.nodes]
    assert_that(filter_names).contains('columnfilter', 'rowfilter')


@pytest.mark.parametrize('tables_fixture_name', ['session_s3_dataset1_tables'])
def test_list_table_data_filters_unauthorized(client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    assert_that(list_table_data_filters).raises(GqlError).when_called_with(client2, table_uri).contains(
        'UnauthorizedOperation', 'LIST_TABLE_DATA_FILTERS', table_uri
    )


@pytest.mark.parametrize('tables_fixture_name', ['session_s3_dataset1_tables'])
def test_delete_table_data_filter_unauthorized(client1, client2, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    filters = list_table_data_filters(client1, table_uri)
    assert_that(delete_table_data_filter).raises(GqlError).when_called_with(
        client2, filters.nodes[0].filterUri
    ).contains('UnauthorizedOperation', 'DELETE_TABLE_DATA_FILTER', table_uri)


@pytest.mark.parametrize(
    'tables_fixture_name',
    [
        pytest.param('session_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f1'])),
        pytest.param('session_imported_sse_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f2'])),
        pytest.param('session_imported_kms_s3_dataset1_tables', marks=pytest.mark.dependency(depends=['f3'])),
    ],
)
def test_delete_table_data_filter(client1, tables_fixture_name, request):
    tables = request.getfixturevalue(tables_fixture_name)
    table_uri = tables[0].tableUri
    filters = list_table_data_filters(client1, table_uri)
    for f in filters:
        assert_that(delete_table_data_filter(client1, f.filterUri)).is_true()
    assert_that(list_table_data_filters(client1, table_uri).nodes).is_empty()
