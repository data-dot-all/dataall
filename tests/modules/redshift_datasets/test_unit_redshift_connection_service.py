from unittest.mock import MagicMock

from assertpy import assert_that

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService


def test_create_redshift_connection_namespace_not_found(env_fixture, api_context_1, group, mock_redshift_serverless):
    # Given a namespace that does not exist
    mock_redshift_serverless.return_value.get_namespace_by_id.return_value = None

    # Then
    assert_that(RedshiftConnectionService.create_redshift_connection).raises(Exception).when_called_with(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection3',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'not-existent-id',
            'workgroup': 'workgroup-id',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-2',
        },
    ).contains('Redshift namespaceId not-existent-id does not exist')


def test_create_redshift_connection_workgroup_not_in_namespace(
    env_fixture, api_context_1, group, mock_redshift_serverless
):
    # Given a workgroup that is not in the namespace
    mock_redshift_serverless.return_value.list_workgroups_in_namespace.return_value = []

    # Then
    assert_that(RedshiftConnectionService.create_redshift_connection).raises(Exception).when_called_with(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection3',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'not-existent-id',
            'workgroup': 'workgroup-id',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-2',
        },
    ).contains('Redshift workgroup workgroup-id does not exist or is not associated to namespace not-existent-id')


def test_create_redshift_connection_cluster_not_found(env_fixture, api_context_1, group, mock_redshift):
    # Given a redshift cluster id that does not exist
    mock_redshift.return_value.describe_cluster.return_value = False

    # Then
    assert_that(RedshiftConnectionService.create_redshift_connection).raises(Exception).when_called_with(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection3',
            'redshiftType': 'cluster',
            'clusterId': 'cluster-id',
            'nameSpaceId': None,
            'workgroup': None,
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-2',
        },
    ).contains('Redshift cluster cluster-id does not exist or cannot be accessed with these parameters')


def test_create_redshift_connection_database_not_found(
    env_fixture, api_context_1, group, mock_redshift, mock_redshift_data
):
    # Given a redshift cluster id
    mock_redshift_data.return_value.get_redshift_connection_database.side_effect = Exception

    # Then
    assert_that(RedshiftConnectionService.create_redshift_connection).raises(Exception).when_called_with(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection3',
            'redshiftType': 'cluster',
            'clusterId': 'cluster-id',
            'nameSpaceId': None,
            'workgroup': None,
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-2',
        },
    ).contains('Redshift database database_1 does not exist or cannot be accessed with these parameters')


def test_create_redshift_serverless_connection(connection1_serverless):
    # When connection is created
    # Then
    assert_that(connection1_serverless).is_not_none()
    assert_that(connection1_serverless.connectionUri).is_not_none()
    assert_that(connection1_serverless.redshiftType).is_equal_to('serverless')


def test_create_redshift_cluster_connection(connection2_cluster):
    # When connection is created
    # Then
    assert_that(connection2_cluster).is_not_none()
    assert_that(connection2_cluster.connectionUri).is_not_none()
    assert_that(connection2_cluster.redshiftType).is_equal_to('cluster')


def test_get_redshift_connection(connection1_serverless, api_context_1):
    # When
    connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=connection1_serverless.connectionUri)

    # Then
    assert_that(connection).is_not_none()
    assert_that(connection.connectionUri).is_equal_to(connection1_serverless.connectionUri)
    assert_that(connection.redshiftType).is_equal_to('serverless')


def test_get_redshift_connection_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.get_redshift_connection_by_uri).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)


def test_delete_redshift_connection(api_context_1, env_fixture, group, mock_redshift_serverless, mock_redshift_data):
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection-to-delete',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'XXXXXXXXXXXXXX',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-1',
        },
    )
    # When
    response = RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    # Then
    assert_that(response).is_true()


def test_delete_redshift_connection_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.delete_redshift_connection).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'DELETE_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)


def test_list_environment_redshift_connections(connection1_serverless, connection2_cluster, api_context_1, env_fixture):
    # When
    response = RedshiftConnectionService.list_environment_redshift_connections(
        uri=env_fixture.environmentUri, filter={}
    )
    # Then
    assert_that(response).contains_entry(count=2)
    assert_that(response).contains_key('page', 'pages', 'pageSize', 'nodes', 'count')
    connections = [conn.connectionUri for conn in response['nodes']]
    assert_that(connections).is_equal_to([connection1_serverless.connectionUri, connection2_cluster.connectionUri])


def test_list_environment_redshift_connections_with_filter(
    connection1_serverless, connection2_cluster, api_context_1, env_fixture
):
    # When
    response = RedshiftConnectionService.list_environment_redshift_connections(
        uri=env_fixture.environmentUri, filter={'term': connection1_serverless.name}
    )
    # Then
    assert_that(response).contains_entry(count=1)
    assert_that(response).contains_key('page', 'pages', 'pageSize', 'nodes')
    connections = [conn.connectionUri for conn in response['nodes']]
    assert_that(connections).is_equal_to([connection1_serverless.connectionUri])


def test_list_environment_redshift_connections_unauthorized(
    connection1_serverless, connection2_cluster, api_context_2, env_fixture
):
    # When
    assert_that(RedshiftConnectionService.list_environment_redshift_connections).raises(Exception).when_called_with(
        uri=env_fixture.environmentUri, filter={}
    ).contains('UnauthorizedOperation', 'LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS', env_fixture.environmentUri)


def test_list_connection_schemas(connection1_serverless, api_context_1, mock_redshift_data):
    # When
    response = RedshiftConnectionService.list_connection_schemas(uri=connection1_serverless.connectionUri)
    assert_that(response).contains('public', 'dev')


def test_list_connection_schemas_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.list_connection_schemas).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)


def test_list_schema_tables(connection1_serverless, api_context_1, mock_redshift_data):
    # When
    response = RedshiftConnectionService.list_schema_tables(uri=connection1_serverless.connectionUri, schema='schema1')
    assert_that(response).is_length(4)


def test_list_schema_tables_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.list_schema_tables).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)
