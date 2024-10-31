from assertpy import assert_that

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_connection_permissions import REDSHIFT_GRANTABLE_PERMISSIONS


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


def test_create_redshift_connection_cluster_not_encrypted(env_fixture, api_context_1, group, mock_redshift):
    # Given a redshift cluster id that is not encrypted
    mock_redshift.return_value.describe_cluster.return_value = {
        'ClusterIdentifier': 'cluster_id_1',
        'ClusterStatus': 'available',
        'Encrypted': False,
    }

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
    assert_that(connection1_serverless.connectionType).is_equal_to('DATA_USER')


def test_create_redshift_cluster_connection(connection2_cluster):
    # When connection is created
    # Then
    assert_that(connection2_cluster).is_not_none()
    assert_that(connection2_cluster.connectionUri).is_not_none()
    assert_that(connection2_cluster.redshiftType).is_equal_to('cluster')
    assert_that(connection2_cluster.connectionType).is_equal_to('DATA_USER')
    # Then no grantable permissions are added to the DATA_USER connection
    response = RedshiftConnectionService.list_connection_group_permissions(
        uri=connection2_cluster.connectionUri, filter={}
    )
    assert_that(response.get('count', False)).is_equal_to(0)


def test_create_redshift_admin_connection(connection3_admin):
    # When connection is created
    # Then
    assert_that(connection3_admin).is_not_none()
    assert_that(connection3_admin.connectionUri).is_not_none()
    assert_that(connection3_admin.redshiftType).is_equal_to('cluster')
    assert_that(connection3_admin.connectionType).is_equal_to('ADMIN')
    # Then all grantable permissions are added to the ADMIN connection
    response = RedshiftConnectionService.list_connection_group_permissions(
        uri=connection3_admin.connectionUri, filter={}
    )
    assert_that(response.get('count', False)).is_equal_to(1)


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


def test_add_group_permissions(
    connection3_admin, connection3_admin_permissions, invited_group_to_environment, api_context_1, mock_redshift_data
):
    # Given an ADMIN connection
    # When
    assert_that(connection3_admin_permissions.get('count', 0)).is_equal_to(2)
    groups = [g.groupUri for g in connection3_admin_permissions.get('nodes', [])]
    assert_that(groups).contains(connection3_admin.SamlGroupName)
    assert_that(groups).contains(invited_group_to_environment.name)


def test_add_group_permissions_unauthorized(connection3_admin, group2, api_context_2):
    # Given that an unauthorized user tries to add permissions to a connection
    # When/Then
    assert_that(RedshiftConnectionService.add_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, group=group2.name, permissions=REDSHIFT_GRANTABLE_PERMISSIONS
    ).contains('UnauthorizedOperation', 'EDIT_REDSHIFT_CONNECTION_PERMISSIONS', connection3_admin.connectionUri)


def test_add_group_permissions_non_admin_connection(connection2_cluster, group2, api_context_1, mock_redshift_data):
    # Given a DATA_USER connection and another group
    # When/Then
    assert_that(RedshiftConnectionService.add_group_permissions).raises(Exception).when_called_with(
        uri=connection2_cluster.connectionUri, group=group2.name, permissions=REDSHIFT_GRANTABLE_PERMISSIONS
    ).contains('InvalidInput', connection2_cluster.connectionType, 'Only ADMIN connections')


def test_add_group_permissions_invalid_permissions(connection3_admin, group2, api_context_1):
    # Given an invalid set of permissions
    invalid_permissions = ['INVALID_PERMISSION']
    # When/Then
    assert_that(RedshiftConnectionService.add_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, group=group2.name, permissions=invalid_permissions
    ).contains('InvalidInput', invalid_permissions[0], 'grantable permissions')


def test_add_group_permissions_invalid_team(connection3_admin, group3, api_context_1):
    # Given a Team that does not belong to environment, group3
    # When/Then
    assert_that(RedshiftConnectionService.add_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, group=group3.name, permissions=REDSHIFT_GRANTABLE_PERMISSIONS
    ).contains('InvalidInput', group3.name, 'team invited')


def test_delete_group_permissions(connection3_admin, invited_group_to_environment, api_context_1, mock_redshift_data):
    # Given
    RedshiftConnectionService.add_group_permissions(
        uri=connection3_admin.connectionUri,
        group=invited_group_to_environment.name,
        permissions=REDSHIFT_GRANTABLE_PERMISSIONS,
    )
    # When
    response = RedshiftConnectionService.delete_group_permissions(
        uri=connection3_admin.connectionUri, group=invited_group_to_environment.name
    )
    # Then
    assert_that(response).is_true()
    # When
    response = RedshiftConnectionService.list_connection_group_permissions(
        uri=connection3_admin.connectionUri, filter={}
    )
    assert_that(response).contains_entry(count=1)


def test_delete_group_permissions_unauthorized(connection3_admin, connection3_admin_permissions, group2, api_context_2):
    # When/Then
    assert_that(RedshiftConnectionService.delete_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, group=group2.name
    ).contains('UnauthorizedOperation', 'EDIT_REDSHIFT_CONNECTION_PERMISSIONS', connection3_admin.connectionUri)


def test_delete_group_permissions_owner_team(connection3_admin, api_context_1):
    # When/Then
    assert_that(RedshiftConnectionService.delete_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, group=connection3_admin.SamlGroupName
    ).contains('InvalidInput', connection3_admin.SamlGroupName, 'EXCEPT the connection owners')


def test_delete_group_permissions_non_admin_connection(connection1_serverless, group2, api_context_1):
    # When/Then
    assert_that(RedshiftConnectionService.delete_group_permissions).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri, group=group2.name
    ).contains('InvalidInput', connection1_serverless.connectionType, 'Only ADMIN connections')


def test_list_connection_group_permissions(
    connection3_admin, connection3_admin_permissions, api_context_1, mock_redshift_data
):
    # When
    response = RedshiftConnectionService.list_connection_group_permissions(
        uri=connection3_admin.connectionUri, filter={}
    )
    # Then
    assert_that(response).contains_entry(count=2)


def test_list_connection_group_permissions_unauthorized(connection3_admin, api_context_2):
    # When/Then
    assert_that(RedshiftConnectionService.list_connection_group_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, filter={}
    ).contains('UnauthorizedOperation', 'EDIT_REDSHIFT_CONNECTION_PERMISSIONS', connection3_admin.connectionUri)


def test_list_connection_group_no_permissions(
    connection3_admin, env_fixture, environment_group, api_context_1, mock_redshift_data, group, group2, group3, group4
):
    # Given group1=connection3_admin.SamlGroupName
    # group2 and group3 are part of the environment
    # group4 is not part of the environment
    env_g2 = environment_group(env_fixture, group2.name)
    env_g3 = environment_group(env_fixture, group3.name)

    # When
    response = RedshiftConnectionService.list_connection_group_no_permissions(
        uri=connection3_admin.connectionUri, filter={}
    )
    # Then only group2 and group3 are part of the environment but do not have permissions
    assert_that(len(response)).is_equal_to(2)
    assert_that(response).contains_only(group2.name, group3.name)


def test_list_connection_group_no_permissions_unauthorized(connection3_admin, api_context_2):
    # When/Then
    assert_that(RedshiftConnectionService.list_connection_group_no_permissions).raises(Exception).when_called_with(
        uri=connection3_admin.connectionUri, filter={}
    ).contains('UnauthorizedOperation', 'EDIT_REDSHIFT_CONNECTION_PERMISSIONS', connection3_admin.connectionUri)


def test_list_connection_group_no_permissions_non_admin_connection(connection1_serverless, api_context_1):
    # When/Then
    assert_that(RedshiftConnectionService.list_connection_group_no_permissions).raises(Exception).when_called_with(
        uri=connection1_serverless.connectionUri, filter={}
    ).contains('InvalidInput', connection1_serverless.connectionType, 'Only ADMIN connections')
