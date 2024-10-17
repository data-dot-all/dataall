from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.redshift_datasets.connection_queries import list_redshift_schema_tables
from integration_tests.modules.redshift_datasets.dataset_queries import (
    list_redshift_dataset_tables,
    import_redshift_dataset,
    update_redshift_dataset,
    delete_redshift_dataset,
    update_redshift_dataset_table,
    add_redshift_dataset_tables,
    delete_redshift_dataset_table,
    get_redshift_dataset,
    get_redshift_dataset_table,
    get_redshift_dataset_table_columns,
    list_redshift_schema_dataset_tables,
)
from integration_tests.modules.redshift_datasets.global_conftest import (
    REDSHIFT_SCHEMA,
    REDSHIFT_TABLE1,
    REDSHIFT_TABLE2,
)


def test_import_redshift_serverless_dataset_with_table(client1, session_redshift_dataset_serverless):
    assert_that(session_redshift_dataset_serverless.datasetUri).is_not_none()
    tables = list_redshift_dataset_tables(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(tables.count).is_equal_to(1)
    assert_that(tables.nodes[0].name).is_equal_to(REDSHIFT_TABLE1)


def test_import_redshift_cluster_dataset_without_table(client5, session_redshift_dataset_cluster):
    assert_that(session_redshift_dataset_cluster.datasetUri).is_not_none()
    tables = list_redshift_dataset_tables(client=client5, dataset_uri=session_redshift_dataset_cluster.datasetUri)
    assert_that(tables.count).is_equal_to(0)


def test_import_redshift_unauthorized(
    client2, user1, group1, session_env1, org1, session_connection_serverless_data_user
):
    assert_that(import_redshift_dataset).raises(GqlError).when_called_with(
        client=client2,
        label='Error-Test-Redshift-Serverless',
        org_uri=org1.organizationUri,
        env_uri=session_env1.environmentUri,
        description='Error',
        tags=[],
        owner=user1.username,
        group_uri=group1,
        confidentiality='Secret',
        auto_approval_enabled=False,
        connection_uri=session_connection_serverless_data_user.connectionUri,
        schema=REDSHIFT_SCHEMA,
        tables=[],
    ).contains('UnauthorizedOperation', 'IMPORT_REDSHIFT_DATASET', session_env1.environmentUri)


def test_import_redshift_dataset_invalid_connection_type(
    client1, user1, group1, session_env1, org1, session_connection_serverless_admin
):
    assert_that(import_redshift_dataset).raises(GqlError).when_called_with(
        client=client1,
        label='Error-Test-Redshift-Serverless',
        org_uri=org1.organizationUri,
        env_uri=session_env1.environmentUri,
        description='Error',
        tags=[],
        owner=user1.username,
        group_uri=group1,
        confidentiality='Secret',
        auto_approval_enabled=False,
        connection_uri=session_connection_serverless_admin.connectionUri,
        schema=REDSHIFT_SCHEMA,
        tables=[],
    ).contains('InvalidInput', 'Connection', 'Only DATA_USER')


def test_update_redshift_dataset(client1, session_redshift_dataset_serverless):
    updated_desc = 'Updated Description'
    response = update_redshift_dataset(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, description=updated_desc
    )
    assert_that(response.description).is_equal_to(updated_desc)


def test_update_redshift_dataset_unauthorized(client2, session_redshift_dataset_serverless):
    assert_that(update_redshift_dataset).raises(GqlError).when_called_with(
        client=client2, dataset_uri=session_redshift_dataset_serverless.datasetUri, description='Updated Description'
    ).contains('UnauthorizedOperation', 'UPDATE_REDSHIFT_DATASET', session_redshift_dataset_serverless.datasetUri)


def test_delete_redshift_dataset(
    user5, group5, client5, session_cross_acc_env_1, org1, session_connection_cluster_data_user
):
    dataset = import_redshift_dataset(
        client=client5,
        label='Test-Redshift-to-Delete',
        org_uri=org1.organizationUri,
        env_uri=session_cross_acc_env_1.environmentUri,
        description='Used for integration test',
        tags=['delete'],
        owner=user5.username,
        group_uri=group5,
        confidentiality='Secret',
        auto_approval_enabled=False,
        connection_uri=session_connection_cluster_data_user.connectionUri,
        schema=REDSHIFT_SCHEMA,
        tables=[],
    )
    assert_that(dataset.datasetUri).is_not_none()
    response = delete_redshift_dataset(client=client5, dataset_uri=dataset.datasetUri)
    assert_that(response).is_true()


def test_delete_redshift_dataset_unauthorized(client2, session_redshift_dataset_serverless):
    assert_that(delete_redshift_dataset).raises(GqlError).when_called_with(
        client=client2, dataset_uri=session_redshift_dataset_serverless.datasetUri
    ).contains('UnauthorizedOperation', 'DELETE_REDSHIFT_DATASET', session_redshift_dataset_serverless.datasetUri)


def test_add_redshift_dataset_tables(client1, session_redshift_dataset_serverless):
    initial_number_of_tables = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri
    ).count
    response = add_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, tables=[REDSHIFT_TABLE2]
    )
    assert_that(response.successTables).contains(REDSHIFT_TABLE2)
    assert_that(response.errorTables).is_empty()
    tables = list_redshift_dataset_tables(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(tables.count).is_equal_to(initial_number_of_tables + 1)


def test_add_redshift_dataset_tables_invalid_table(client1, session_redshift_dataset_serverless):
    initial_number_of_tables = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri
    ).count
    response = add_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, tables=['does-not-exist']
    )
    assert_that(response.successTables).is_empty()
    assert_that(response.errorTables).contains('does-not-exist')
    tables = list_redshift_dataset_tables(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(tables.count).is_equal_to(initial_number_of_tables)


def test_add_redshift_dataset_tables_unauthorized(client2, session_redshift_dataset_serverless):
    assert_that(add_redshift_dataset_tables).raises(GqlError).when_called_with(
        client=client2, dataset_uri=session_redshift_dataset_serverless.datasetUri, tables=[REDSHIFT_TABLE2]
    ).contains('UnauthorizedOperation', 'ADD_TABLES_REDSHIFT_DATASET', session_redshift_dataset_serverless.datasetUri)


def test_update_redshift_dataset_table(client1, session_redshift_dataset_serverless_table, session_id):
    new_desc = f'Updated Description {session_id}'
    response = update_redshift_dataset_table(
        client=client1, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri, description=new_desc
    )
    assert_that(response.description).is_equal_to(new_desc)


def test_update_redshift_dataset_table_unauthorized(client2, session_redshift_dataset_serverless_table):
    assert_that(update_redshift_dataset_table).raises(GqlError).when_called_with(
        client=client2,
        rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri,
        description='Updated Description',
    ).contains(
        'UnauthorizedOperation', 'UPDATE_REDSHIFT_DATASET_TABLE', session_redshift_dataset_serverless_table.rsTableUri
    )


def test_delete_redshift_dataset_table(client1, session_redshift_dataset_serverless):
    table_2 = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, term=REDSHIFT_TABLE2
    )
    if table_2.count == 0:
        response = add_redshift_dataset_tables(
            client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, tables=[REDSHIFT_TABLE2]
        )
        assert_that(response.successTables).contains(REDSHIFT_TABLE2)
    table_2 = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, term=REDSHIFT_TABLE2
    ).nodes[0]
    response = delete_redshift_dataset_table(client=client1, rs_table_uri=table_2.rsTableUri)
    assert_that(response).is_true()


def test_delete_redshift_dataset_table_unauthorized(client2, session_redshift_dataset_serverless_table):
    assert_that(delete_redshift_dataset_table).raises(GqlError).when_called_with(
        client=client2, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri
    ).contains(
        'UnauthorizedOperation', 'DELETE_REDSHIFT_DATASET_TABLE', session_redshift_dataset_serverless_table.rsTableUri
    )


def test_get_redshift_dataset(client1, session_redshift_dataset_serverless):
    response = get_redshift_dataset(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(response).contains_entry(
        datasetUri=session_redshift_dataset_serverless.datasetUri,
        schema=REDSHIFT_SCHEMA,
    )
    assert_that(response.connection.connectionUri).is_equal_to(
        session_redshift_dataset_serverless.connection.connectionUri
    )


def test_get_redshift_dataset_unauthorized(client2, session_redshift_dataset_serverless):
    assert_that(get_redshift_dataset).raises(GqlError).when_called_with(
        client=client2, dataset_uri=session_redshift_dataset_serverless.datasetUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', session_redshift_dataset_serverless.datasetUri)


def test_list_redshift_dataset_tables(client1, session_redshift_dataset_serverless):
    response = list_redshift_dataset_tables(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(response).contains_key('count', 'page', 'pages', 'nodes')


def test_list_redshift_dataset_tables_unauthorized(client2, session_redshift_dataset_serverless):
    assert_that(list_redshift_dataset_tables).raises(GqlError).when_called_with(
        client=client2, dataset_uri=session_redshift_dataset_serverless.datasetUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', session_redshift_dataset_serverless.datasetUri)


def test_get_redshift_dataset_table(client1, session_redshift_dataset_serverless_table):
    response = get_redshift_dataset_table(
        client=client1, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri
    )
    assert_that(response).contains_entry(
        rsTableUri=session_redshift_dataset_serverless_table.rsTableUri, name=REDSHIFT_TABLE1
    )


def test_get_redshift_dataset_table_unauthorized(client2, session_redshift_dataset_serverless_table):
    assert_that(get_redshift_dataset_table).raises(GqlError).when_called_with(
        client=client2, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri
    ).contains(
        'UnauthorizedOperation', 'GET_REDSHIFT_DATASET_TABLE', session_redshift_dataset_serverless_table.rsTableUri
    )


def test_get_redshift_dataset_table_columns(client1, session_redshift_dataset_serverless_table):
    response = get_redshift_dataset_table_columns(
        client=client1, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri
    )
    assert_that(response).contains_key('count', 'page', 'pages', 'nodes')


def test_get_redshift_dataset_table_columns_unauthorized(client2, session_redshift_dataset_serverless_table):
    assert_that(get_redshift_dataset_table_columns).raises(GqlError).when_called_with(
        client=client2, rs_table_uri=session_redshift_dataset_serverless_table.rsTableUri
    ).contains(
        'UnauthorizedOperation', 'GET_REDSHIFT_DATASET_TABLE', session_redshift_dataset_serverless_table.rsTableUri
    )


def test_list_redshift_schema_dataset_tables(client1, session_redshift_dataset_serverless):
    added_tables = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri
    )
    schema_tables = list_redshift_schema_tables(
        client=client1,
        connection_uri=session_redshift_dataset_serverless.connection.connectionUri,
        schema=REDSHIFT_SCHEMA,
    )
    response = list_redshift_schema_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri
    )
    assert_that(len(response)).is_equal_to(len(schema_tables))
    response_added_tables = [table.name for table in response if table.alreadyAdded]
    assert_that(response_added_tables).contains(*[table.name for table in added_tables.nodes])
