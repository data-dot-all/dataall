from assertpy import assert_that
import pytest

from integration_tests.errors import GqlError
from integration_tests.modules.redshift_datasets.connection_queries import (
    create_redshift_connection,
    delete_redshift_connection,
    add_redshift_connection_group_permissions,
    delete_redshift_connection_group_permissions,
    list_environment_redshift_connections,
    list_redshift_connection_schemas,
    list_redshift_schema_tables,
    list_redshift_connection_group_permissions,
    list_redshift_connection_group_no_permissions,
)
from integration_tests.modules.redshift_datasets.global_conftest import REDSHIFT_DATABASE, REDSHIFT_SCHEMA


@pytest.mark.parametrize(
    'connection_fixture_name, connection_type, redshift_type',
    [
        ('session_connection_serverless_data_user', 'DATA_USER', 'serverless'),
        ('session_connection_cluster_data_user', 'DATA_USER', 'cluster'),
        ('session_connection_serverless_admin', 'ADMIN', 'serverless'),
        ('session_connection_cluster_admin', 'ADMIN', 'cluster'),
    ],
)
def test_create_connection(connection_fixture_name, connection_type, redshift_type, request):
    connection = request.getfixturevalue(connection_fixture_name)
    assert_that(connection.connectionUri).is_not_none()
    assert_that(connection.connectionType).is_equal_to(connection_type)
    assert_that(connection.redshiftType).is_equal_to(redshift_type)


def test_create_serverless_connection_namespace_does_not_exist(client1, group1, session_env1, redshift_connections):
    connection_data = redshift_connections['connection_serverless_data_user_session_env1']
    error_namespace_id = 'doesnotexist'
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client1,
        connection_name='errorConnection',
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
        redshift_type='serverless',
        connection_type='DATA_USER',
        namespace_id=error_namespace_id,
        workgroup=connection_data.workgroup,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('Redshift namespaceId', error_namespace_id, 'not exist')


def test_create_serverless_connection_workgroup_not_found(client1, group1, session_env1, redshift_connections):
    connection_data = redshift_connections['connection_serverless_data_user_session_env1']
    error_workgroup = 'doesnotexist'
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client1,
        connection_name='errorConnection',
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
        redshift_type='serverless',
        connection_type='DATA_USER',
        namespace_id=connection_data.namespace_id,
        workgroup=error_workgroup,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('Redshift workgroup', error_workgroup, 'not exist')


def test_create_cluster_connection_cluster_not_found(client5, group5, session_cross_acc_env_1, redshift_connections):
    connection_data = redshift_connections['connection_cluster_data_user_session_cross_acc_env_1']
    error_cluster_id = 'doesnotexist'
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client5,
        connection_name='errorConnection',
        environment_uri=session_cross_acc_env_1.environmentUri,
        group_uri=group5,
        redshift_type='cluster',
        connection_type='DATA_USER',
        cluster_id=error_cluster_id,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('Redshift cluster', error_cluster_id, 'not exist')


def test_create_cluster_connection_cluster_not_encrypted():
    # TODO: we need to decide if we want to create an extra cluster that is not encrypted
    pass


def test_create_connection_database_not_found(client5, group5, session_cross_acc_env_1, redshift_connections):
    connection_data = redshift_connections['connection_cluster_data_user_session_cross_acc_env_1']
    error_database = 'doesnotexist'
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client5,
        connection_name='errorConnection',
        environment_uri=session_cross_acc_env_1.environmentUri,
        group_uri=group5,
        redshift_type='cluster',
        connection_type='DATA_USER',
        cluster_id=connection_data.cluster_id,
        database=error_database,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('Redshift database', error_database, 'not exist')


def test_create_connection_unauthorized(client1, group1, session_cross_acc_env_1, redshift_connections):
    connection_data = redshift_connections['connection_cluster_data_user_session_cross_acc_env_1']
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client1,
        connection_name='errorConnection',
        environment_uri=session_cross_acc_env_1.environmentUri,
        group_uri=group1,
        redshift_type='cluster',
        connection_type='DATA_USER',
        cluster_id=connection_data.cluster_id,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('UnauthorizedOperation', 'CREATE_REDSHIFT_CONNECTION', session_cross_acc_env_1.environmentUri)


def test_delete_connection(client5, group5, session_cross_acc_env_1, redshift_connections):
    connection_data = redshift_connections['connection_cluster_data_user_session_cross_acc_env_1']
    connection = create_redshift_connection(
        client=client5,
        connection_name='errorConnection',
        environment_uri=session_cross_acc_env_1.environmentUri,
        group_uri=group5,
        redshift_type='cluster',
        connection_type='DATA_USER',
        cluster_id=connection_data.cluster_id,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    )
    response = delete_redshift_connection(
        client=client5,
        connection_uri=connection.connectionUri,
    )
    assert_that(response).is_true()


def test_delete_connection_unauthorized(client2, session_connection_serverless_admin):
    assert_that(delete_redshift_connection).raises(GqlError).when_called_with(
        client=client2,
        connection_uri=session_connection_serverless_admin.connectionUri,
    ).contains('UnauthorizedOperation', 'DELETE_REDSHIFT_CONNECTION', session_connection_serverless_admin.connectionUri)


def test_add_connection_group_permissions(client1, group5, session_connection_serverless_admin_group_with_permissions):
    assert_that(session_connection_serverless_admin_group_with_permissions).is_equal_to(group5)


def test_add_connection_group_permissions_unauthorized(client2, group5, session_connection_serverless_admin):
    assert_that(add_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client2,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group5,
        permissions=['CREATE_SHARE_REQUEST_WITH_CONNECTION'],
    ).contains(
        'UnauthorizedOperation',
        'EDIT_REDSHIFT_CONNECTION_PERMISSIONS',
        session_connection_serverless_admin.connectionUri,
    )


def test_add_connection_group_permissions_invalid_connection_type(
    client1, group5, session_connection_serverless_data_user
):
    assert_that(add_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client1,
        connection_uri=session_connection_serverless_data_user.connectionUri,
        group_uri=group5,
        permissions=['CREATE_SHARE_REQUEST_WITH_CONNECTION'],
    ).contains('InvalidInput', 'ConnectionType', session_connection_serverless_data_user.connectionType)


def test_add_connection_group_permissions_invalid_permissions(client1, group5, session_connection_serverless_admin):
    assert_that(add_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group5,
        permissions=['INVALID_PERMISSION'],
    ).contains('InvalidInput', 'INVALID_PERMISSION', 'Permissions')


def test_add_connection_group_permissions_invalid_group(client1, group3, session_connection_serverless_admin):
    assert_that(add_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group3,
        permissions=['CREATE_SHARE_REQUEST_WITH_CONNECTION'],
    ).contains('InvalidInput', group3, 'Team')


def test_delete_connection_group_permissions(client1, group5, session_connection_serverless_admin):
    response = delete_redshift_connection_group_permissions(
        client=client1, connection_uri=session_connection_serverless_admin.connectionUri, group_uri=group5
    )
    assert_that(response).is_true()
    # Revert changes
    response = add_redshift_connection_group_permissions(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group5,
        permissions=['CREATE_SHARE_REQUEST_WITH_CONNECTION'],
    )
    assert_that(response).is_true()


def test_delete_connection_group_permissions_unauthorized(client2, group3, session_connection_serverless_admin):
    assert_that(delete_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client2,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group3,
    ).contains(
        'UnauthorizedOperation',
        'EDIT_REDSHIFT_CONNECTION_PERMISSIONS',
        session_connection_serverless_admin.connectionUri,
    )


def test_delete_connection_group_permissions_invalid_connection_type(
    client1, group3, session_connection_serverless_data_user
):
    assert_that(delete_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client1,
        connection_uri=session_connection_serverless_data_user.connectionUri,
        group_uri=group3,
    ).contains('InvalidInput', 'ConnectionType', session_connection_serverless_data_user.connectionType)


def test_delete_connection_group_permissions_invalid_group(client1, group1, session_connection_serverless_admin):
    assert_that(delete_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        group_uri=group1,
    ).contains('InvalidInput', 'Team', group1, 'EXCEPT the connection owners')


def test_list_redshift_environment_connections(
    client1, group1, session_env1, session_connection_serverless_admin, session_connection_serverless_data_user
):
    response = list_environment_redshift_connections(
        client=client1,
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
    )
    assert_that(response.count).is_equal_to(2)
    assert_that(response.nodes).extracting('connectionUri').contains(
        session_connection_serverless_admin.connectionUri, session_connection_serverless_data_user.connectionUri
    )
    response = list_environment_redshift_connections(
        client=client1,
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
        connection_type='DATA_USER',
    )
    assert_that(response.count).is_equal_to(1)
    assert_that(response.nodes).extracting('connectionUri').contains(
        session_connection_serverless_data_user.connectionUri
    )
    assert_that(response.nodes).extracting('connectionUri').does_not_contain(
        session_connection_serverless_admin.connectionUri
    )


def test_list_redshift_environment_connections_unauthorized(client2, group1, session_env1):
    assert_that(list_environment_redshift_connections).raises(GqlError).when_called_with(
        client=client2,
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
    ).contains(
        'UnauthorizedOperation',
        'LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS',
        session_env1.environmentUri,
    )


def test_list_redshift_connection_schemas(client1, session_connection_serverless_admin):
    response = list_redshift_connection_schemas(
        client=client1, connection_uri=session_connection_serverless_admin.connectionUri
    )
    assert_that(len(response)).is_greater_than_or_equal_to(1)
    assert_that(response).contains(REDSHIFT_SCHEMA)


def test_list_redshift_connection_schemas_unauthorized(client2, session_connection_serverless_admin):
    assert_that(list_redshift_connection_schemas).raises(GqlError).when_called_with(
        client=client2, connection_uri=session_connection_serverless_admin.connectionUri
    ).contains(
        'UnauthorizedOperation',
        'GET_REDSHIFT_CONNECTION',
        session_connection_serverless_admin.connectionUri,
    )


def test_list_redshift_schema_tables(client1, session_connection_serverless_admin):
    response = list_redshift_schema_tables(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        schema=REDSHIFT_SCHEMA,
    )
    assert_that(len(response)).is_greater_than_or_equal_to(1)
    assert_that(response[0]).contains_key('name', 'type')


def test_list_redshift_schema_tables_unauthorized(client2, session_connection_serverless_admin):
    assert_that(list_redshift_schema_tables).raises(GqlError).when_called_with(
        client=client2, connection_uri=session_connection_serverless_admin.connectionUri, schema=REDSHIFT_SCHEMA
    ).contains(
        'UnauthorizedOperation',
        'GET_REDSHIFT_CONNECTION',
        session_connection_serverless_admin.connectionUri,
    )


def test_list_redshift_connection_group_permissions(
    client1, group1, session_connection_serverless_admin, session_connection_serverless_admin_group_with_permissions
):
    response = list_redshift_connection_group_permissions(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
    )
    assert_that(response.count).is_equal_to(2)
    assert_that(response.nodes).extracting('groupUri').contains(
        group1, session_connection_serverless_admin_group_with_permissions
    )
    response = list_redshift_connection_group_permissions(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
        filter={'term': session_connection_serverless_admin_group_with_permissions},
    )
    assert_that(response.count).is_equal_to(1)
    assert_that(response.nodes).extracting('groupUri').contains(
        session_connection_serverless_admin_group_with_permissions
    )


def test_list_redshift_connection_group_permissions_unauthorized(client2, session_connection_serverless_admin):
    assert_that(list_redshift_connection_group_permissions).raises(GqlError).when_called_with(
        client=client2, connection_uri=session_connection_serverless_admin.connectionUri
    ).contains(
        'UnauthorizedOperation',
        'EDIT_REDSHIFT_CONNECTION_PERMISSIONS',
        session_connection_serverless_admin.connectionUri,
    )


def test_list_redshift_connection_group_no_permissions(
    client1, group1, session_connection_serverless_admin, session_connection_serverless_admin_group_with_permissions
):
    response = list_redshift_connection_group_no_permissions(
        client=client1,
        connection_uri=session_connection_serverless_admin.connectionUri,
    )
    assert_that(response).does_not_contain(session_connection_serverless_admin_group_with_permissions, group1)
    assert_that(response).is_not_none()


def test_list_redshift_connection_group_no_permissions_unauthorized(client2, session_connection_serverless_admin):
    assert_that(list_redshift_connection_group_no_permissions).raises(GqlError).when_called_with(
        client=client2, connection_uri=session_connection_serverless_admin.connectionUri
    ).contains(
        'UnauthorizedOperation',
        'EDIT_REDSHIFT_CONNECTION_PERMISSIONS',
        session_connection_serverless_admin.connectionUri,
    )
