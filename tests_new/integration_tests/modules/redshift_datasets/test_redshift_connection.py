from assertpy import assert_that
import pytest

from integration_tests.errors import GqlError
from integration_tests.modules.redshift_datasets.connection_queries import (
    create_redshift_connection,
    delete_redshift_connection,
)
from integration_tests.modules.redshift_datasets.global_conftest import REDSHIFT_DATABASE


@pytest.mark.parametrize(
    'connection_fixture_name, connection_type, redshift_type',
    [
        ('session_connection1_serverless_data_user', 'DATA_USER', 'serverless'),
        ('session_connection2_cluster_data_user', 'DATA_USER', 'cluster'),
        ('session_connection3_serverless_admin', 'ADMIN', 'serverless'),
        ('session_connection4_cluster_admin', 'ADMIN', 'cluster'),
    ],
)
def test_create_connection(client1, connection_fixture_name, connection_type, redshift_type, request):
    connection = request.getfixturevalue(connection_fixture_name)
    assert_that(connection.connectionUri).is_not_none()
    assert_that(connection.connectionType).is_equal_to(connection_type)
    assert_that(connection.redshiftType).is_equal_to(redshift_type)


def test_create_serverless_connection_namespace_does_not_exist(client1, group1, session_env1, testdata):
    connection_data = testdata.redshift_connections.get('connection_1')
    ERROR_NAMESPACE_ID = 'doesNotExistNamespace'
    assert_that(create_redshift_connection).raises(GqlError).when_called_with(
        client=client1,
        connection_name='errorConnection',
        environment_uri=session_env1.environmentUri,
        group_uri=group1,
        redshift_type='serverless',
        namespace_id=ERROR_NAMESPACE_ID,
        workgroup=connection_data.workgroup,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    ).contains('Redshift namespaceId', ERROR_NAMESPACE_ID, 'not exist')


def test_create_serverless_connection_workgroup_not_found():
    pass


def test_create_cluster_connection_cluster_not_found():
    pass


def test_create_cluster_connection_cluster_not_encrypted():
    pass


def test_create_connection_database_not_found():
    pass


def test_create_connection_unauthorized():
    pass
