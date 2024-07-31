from assertpy import assert_that
from unittest.mock import MagicMock, patch
from .conftest import MockRedshiftClient, MockRedshiftDataClient, MockRedshiftServerlessClient
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService


def test_create_redshift_connection_namespace_not_found(env_fixture, api_context_1, group, mocker):
    # Given a namespace that does not exist
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerlessClient.get_namespace_by_id',
        return_value=None,
    )
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


def test_create_redshift_connection_workgroup_not_in_namespace(env_fixture, api_context_1, group, mocker):
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerlessClient.get_namespace_by_id',
        return_value=MockRedshiftServerlessClient().get_namespace_by_id(),
    )
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerlessClient.list_workgroups_in_namespace',
        return_value=[],
    )

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


def test_create_redshift_connection_cluster_not_found(env_fixture, api_context_1, group, mocker):
    # Given a redshift cluster id that does not exist
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift.RedshiftClient.describe_cluster',
        return_value=False,
    )

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


def test_create_redshift_connection_cluster_not_encrypted(env_fixture, api_context_1, group, mocker):
    # Given a redshift cluster id
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift.RedshiftClient.describe_cluster',
        return_value={'ClusterIdentifier': 'cluster_id_1', 'ClusterStatus': 'available', 'Encrypted': False},
    )
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
    ).contains('is not encrypted. Data.all clusters MUST be encrypted')


def test_create_redshift_connection_database_not_found(env_fixture, api_context_1, group, mocker):
    # Given a redshift cluster id
    mock_redshift = MagicMock()
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift.RedshiftClient.describe_cluster',
        return_value=mock_redshift,
        autospec=True,
    )
    mock_redshift.describe_cluster.return_value = MockRedshiftClient().describe_cluster()
    mock_redshift_data = MagicMock()
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_data.RedshiftDataClient',
        return_value=mock_redshift_data,
    )
    mock_redshift_data.get_redshift_connection_database.side_effect = Exception

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


def test_get_redshift_connection(connection1_serverless, api_context_1, patch_redshift):
    # When
    connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=connection1_serverless.connectionUri)

    # Then
    assert_that(connection).is_not_none()
    assert_that(connection.connectionUri).is_equal_to(connection1_serverless.connectionUri)
    assert_that(connection.redshiftType).is_equal_to('serverless')


def test_get_redshift_connection_unauthorized(connection1_serverless, api_context_2, patch_redshift):
    # When
    assert_that(RedshiftConnectionService.get_redshift_connection_by_uri).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)


def test_delete_redshift_connection(api_context_1, env_fixture, group, patch_redshift):
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


def test_delete_redshift_connection_unauthorized(connection1_serverless, api_context_2, patch_redshift):
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


def test_list_connection_schemas(connection1_serverless, api_context_1, patch_redshift):
    # When
    response = RedshiftConnectionService.list_connection_schemas(uri=connection1_serverless.connectionUri)
    assert_that(response).is_equal_to(MockRedshiftDataClient().list_redshift_schemas())


def test_list_connection_schemas_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.list_connection_schemas).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)


def test_list_schema_tables(connection1_serverless, api_context_1, patch_redshift):
    # When
    response = RedshiftConnectionService.list_schema_tables(uri=connection1_serverless.connectionUri, schema='schema1')
    assert_that(response).is_equal_to(MockRedshiftDataClient().list_redshift_tables())


def test_list_schema_tables_unauthorized(connection1_serverless, api_context_2):
    # When
    assert_that(RedshiftConnectionService.list_schema_tables).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_CONNECTION', connection1_serverless.connectionUri)
