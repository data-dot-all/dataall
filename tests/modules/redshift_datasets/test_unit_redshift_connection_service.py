from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService

def test_create_redshift_connection(connection1_serverless):
    # When connection1 is created
    # Then
    assert connection1_serverless
    assert connection1_serverless.connectionUri


def test_create_redshift_connection_namespace_not_found(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerless.get_namespace_by_id',
        return_value=None,
    )
    pass

def test_create_redshift_connection_workgroup_not_in_namespace(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerless.get_namespace_by_id',
        return_value=True,
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerless.list_workgroups_in_namespace',
        return_value=[],
    )

def test_create_redshift_connection_cluster_not_found(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift.Redshift.describe_cluster',
        return_value=False,
    )

def test_create_redshift_connection_serverless_database_not_found(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerless.get_namespace_by_id',
        return_value=True,
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerless.list_workgroups_in_namespace',
        return_value=[],
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_data.RedshiftData.get_redshift_connection_database',
        return_value=False,  # TODO: return exception
    )


def test_create_redshift_connection_cluster_database_not_found(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift.Redshift.describe_cluster',
        return_value=True,
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_data.RedshiftData.get_redshift_connection_database',
        return_value=False, #TODO: return exception
    )

def test_get_redshift_connection(patch_redshift):
    # When
    connection = RedshiftConnectionService.get_redshift_connection_by_uri()

    # Then
    assert connection
    assert connection.connectionUri


def test_delete_redshift_connection():
    # When
    response = RedshiftConnectionService.delete_redshift_connection()
    # Then
    assert response == True

def test_list_environment_redshift_connections(connection1_serverless, connection2_cluster):
    pass

def test_list_environment_redshift_connections_with_filter(connection1_serverless, connection2_cluster):
    pass

def test_list_environment_redshift_connections_non_admin_user(connection1_serverless, connection2_cluster):
    pass


def test_list_connection_schemas(connection1_serverless):
    pass


def test_list_schema_tables(connection1_serverless):
    pass

