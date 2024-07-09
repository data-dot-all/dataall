from assertpy import assert_that

from integration_tests.modules.worksheets.queries import (
    create_worksheet,
    delete_worksheet,
    get_worksheet,
    list_worksheets,
    run_athena_sql_query,
    update_worksheet,
)
from integration_tests.errors import GqlError


def test_create_worksheet(client1, worksheet1):
    assert_that(worksheet1.worksheetUri).is_length(8)
    assert_that(worksheet1.label).is_equal_to('worksheet1')


def test_delete_worksheet(client1, group1, session_id):
    ws = create_worksheet(client1, 'worksheetdelete', group1, tags=[session_id])
    assert assert_that(ws.label).is_equal_to('worksheetdelete')
    response = delete_worksheet(client1, ws.worksheetUri)
    assert_that(response).is_equal_to(True)


def test_delete_worksheet_unauthorized(client2, worksheet1):
    assert_that(delete_worksheet).raises(GqlError).when_called_with(client2, worksheet1.worksheetUri).contains(
        'UnauthorizedOperation', 'DELETE_WORKSHEET'
    )


def test_get_worksheet(client1, group1, worksheet1):
    ws = get_worksheet(client1, worksheet1.worksheetUri)
    assert_that(ws.SamlAdminGroupName).is_equal_to(group1)
    assert_that(ws.worksheetUri).is_equal_to(worksheet1.worksheetUri)


def test_get_worksheet_unauthorized(client2, worksheet1):
    assert_that(get_worksheet).raises(GqlError).when_called_with(client2, worksheet1.worksheetUri).contains(
        'UnauthorizedOperation', 'GET_WORKSHEET'
    )


def test_list_worksheets(client1, worksheet1, session_id):
    response = list_worksheets(client1, term=session_id)
    assert_that(response.count).is_equal_to(1)


def test_list_worksheets_no_admin(client2, worksheet1, session_id):
    response = list_worksheets(client2, term=session_id)
    assert_that(response.count).is_equal_to(0)


# def test_run_athena_sql_query(client1, session_env1, worksheet1):
#     response = run_athena_sql_query(client1, environment_uri=session_env1.environmentUri, worksheet_uri=worksheet1.worksheetUri, query="select * from randomTable")
#     assert response
# def test_run_athena_sql_query_unauthorized(client2, session_env1, worksheet1):
#     assert_that(update_worksheet).raises(GqlError).when_called_with(
#         client2, session_env1.environmentUri, worksheet1.worksheetUri, "select * from random_table"
#     ).contains('UnauthorizedOperation', 'RUN_ATHENA_QUERY')
#


def test_update_worksheet(client1, worksheet1):
    ws = update_worksheet(client1, worksheet1.worksheetUri, worksheet1.label, 'updated desc', worksheet1.tags)
    assert_that(ws.description).is_equal_to('updated desc')


def test_update_worksheet_unauthorized(client2, worksheet1):
    assert_that(update_worksheet).raises(GqlError).when_called_with(
        client2, worksheet1.worksheetUri, worksheet1.label, 'updated desc', worksheet1.tags
    ).contains('UnauthorizedOperation', 'UPDATE_WORKSHEET')
