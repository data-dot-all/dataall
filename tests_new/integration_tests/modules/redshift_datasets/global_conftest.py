import logging

import pytest
from integration_tests.core.stack.utils import check_stack_ready
from integration_tests.conftest import RedshiftConnection
from integration_tests.modules.redshift_datasets.connection_queries import (
    create_redshift_connection,
    delete_redshift_connection,
    add_redshift_connection_group_permissions,
    delete_redshift_connection_group_permissions,
)

log = logging.getLogger(__name__)

REDSHIFT_DATABASE = 'dev'
REDSHIFT_SCHEMA = 'public'


def create_connection(client, env, group, name, conn_type, red_type, connection_data=RedshiftConnection):
    connection = create_redshift_connection(
        client=client,
        connection_name=name,
        connection_type=conn_type,
        environment_uri=env.environmentUri,
        group_uri=group,
        redshift_type=red_type,
        cluster_id=connection_data.cluster_id,
        namespace_id=connection_data.namespace_id,
        workgroup=connection_data.workgroup,
        database=REDSHIFT_DATABASE,
        redshift_user=None,
        secret_arn=connection_data.secret_arn,
    )
    check_stack_ready(
        client=client,
        env_uri=env.environmentUri,
        stack_uri=env.stack.stackUri,
        target_uri=env.environmentUri,
        target_type='environment',
    )
    return connection


"""
- Serverless namespace is deployed in session_env1 account
- Provisioned cluster is deployed in session_cross_acc_env_1
"""


@pytest.fixture(scope='session')
def session_connection_serverless_admin(client1, group1, session_env1, testdata):
    connection = None
    try:
        connection = create_connection(
            client=client1,
            name='connection_serverless_admin_session_env1',
            conn_type='ADMIN',
            env=session_env1,
            group=group1,
            red_type='serverless',
            connection_data=testdata.redshift_connections['connection_serverless_admin_session_env1'],
        )

        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client1, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_connection_serverless_admin_group_with_permissions(client1, group5, session_connection_serverless_admin):
    permissions = None
    try:
        permissions = add_redshift_connection_group_permissions(
            client=client1,
            connection_uri=session_connection_serverless_admin.connectionUri,
            group_uri=group5,
            permissions=['CREATE_SHARE_REQUEST_WITH_CONNECTION'],
        )
        yield group5
    finally:
        if permissions:
            delete_redshift_connection_group_permissions(
                client=client1, connection_uri=session_connection_serverless_admin.connectionUri, group_uri=group5
            )


@pytest.fixture(scope='session')
def session_connection_serverless_data_user(client1, group1, session_env1, testdata):
    connection = None
    try:
        connection = create_connection(
            client=client1,
            name='connection_serverless_data_user_session_env1',
            conn_type='DATA_USER',
            env=session_env1,
            group=group1,
            red_type='serverless',
            connection_data=testdata.redshift_connections['connection_serverless_data_user_session_env1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client1, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_connection_cluster_admin(client5, group5, session_cross_acc_env_1, testdata):
    connection = None
    try:
        connection = create_connection(
            client=client5,
            name='connection_cluster_admin_session_cross_acc_env_1',
            conn_type='ADMIN',
            env=session_cross_acc_env_1,
            group=group5,
            red_type='cluster',
            connection_data=testdata.redshift_connections['connection_cluster_admin_session_cross_acc_env_1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client5, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_connection_cluster_data_user(client5, group5, session_cross_acc_env_1, testdata):
    connection = None
    try:
        connection = create_connection(
            client=client5,
            name='connection_cluster_data_user_session_cross_acc_env_1',
            conn_type='DATA_USER',
            env=session_cross_acc_env_1,
            group=group5,
            red_type='cluster',
            connection_data=testdata.redshift_connections['connection_cluster_data_user_session_cross_acc_env_1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client5, connection_uri=connection.connectionUri)
