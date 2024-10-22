import logging

import pytest
from integration_tests.core.stack.utils import check_stack_ready, check_stack_in_progress
from integration_tests.conftest import RedshiftConnection
from integration_tests.modules.redshift_datasets.connection_queries import (
    create_redshift_connection,
    delete_redshift_connection,
    add_redshift_connection_group_permissions,
    delete_redshift_connection_group_permissions,
)

from integration_tests.modules.redshift_datasets.dataset_queries import (
    import_redshift_dataset,
    delete_redshift_dataset,
    list_redshift_dataset_tables,
    add_redshift_dataset_tables,
)

log = logging.getLogger(__name__)

REDSHIFT_DATABASE = 'dev'
REDSHIFT_SCHEMA = 'public'
REDSHIFT_TABLE1 = 'region'
REDSHIFT_TABLE2 = 'nation'


@pytest.fixture(scope='session')
def redshift_connections(testdata):
    if testdata.redshift_connections:
        return testdata.redshift_connections
    pytest.skip('redshift config is missing')


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
    # The connection creation updates the permissions of the pivot role in the environment stack
    check_stack_in_progress(
        client=client,
        env_uri=env.environmentUri,
        stack_uri=env.stack.stackUri,
        target_uri=env.environmentUri,
        target_type='environment',
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
def session_connection_serverless_admin(client1, group1, session_env1, redshift_connections):
    connection = None
    try:
        connection = create_connection(
            client=client1,
            name='connection_serverless_admin_session_env1',
            conn_type='ADMIN',
            env=session_env1,
            group=group1,
            red_type='serverless',
            connection_data=redshift_connections['connection_serverless_admin_session_env1'],
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
def session_connection_serverless_data_user(client1, group1, session_env1, redshift_connections):
    connection = None
    try:
        connection = create_connection(
            client=client1,
            name='connection_serverless_data_user_session_env1',
            conn_type='DATA_USER',
            env=session_env1,
            group=group1,
            red_type='serverless',
            connection_data=redshift_connections['connection_serverless_data_user_session_env1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client1, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_connection_cluster_admin(client5, group5, session_cross_acc_env_1, redshift_connections):
    connection = None
    try:
        connection = create_connection(
            client=client5,
            name='connection_cluster_admin_session_cross_acc_env_1',
            conn_type='ADMIN',
            env=session_cross_acc_env_1,
            group=group5,
            red_type='cluster',
            connection_data=redshift_connections['connection_cluster_admin_session_cross_acc_env_1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client5, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_connection_cluster_data_user(client5, group5, session_cross_acc_env_1, redshift_connections):
    connection = None
    try:
        connection = create_connection(
            client=client5,
            name='connection_cluster_data_user_session_cross_acc_env_1',
            conn_type='DATA_USER',
            env=session_cross_acc_env_1,
            group=group5,
            red_type='cluster',
            connection_data=redshift_connections['connection_cluster_data_user_session_cross_acc_env_1'],
        )
        yield connection
    finally:
        if connection:
            delete_redshift_connection(client=client5, connection_uri=connection.connectionUri)


@pytest.fixture(scope='session')
def session_redshift_dataset_serverless(
    client1, group1, user1, session_env1, org1, session_connection_serverless_data_user, session_id
):
    dataset = None
    try:
        dataset = import_redshift_dataset(
            client=client1,
            label='session_redshift_serverless_dataset1',
            org_uri=org1.organizationUri,
            env_uri=session_env1.environmentUri,
            description='Used for integration test',
            tags=[session_id],
            owner=user1.username,
            group_uri=group1,
            confidentiality='Unclassified',
            auto_approval_enabled=False,
            connection_uri=session_connection_serverless_data_user.connectionUri,
            schema=REDSHIFT_SCHEMA,
            tables=[REDSHIFT_TABLE1],
        )
        yield dataset
    finally:
        if dataset:
            delete_redshift_dataset(client=client1, dataset_uri=dataset.datasetUri)


@pytest.fixture(scope='session')
def session_redshift_dataset_serverless_table(client1, session_redshift_dataset_serverless):
    tables = list_redshift_dataset_tables(
        client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri, term=REDSHIFT_TABLE1
    )
    yield tables.nodes[0]


@pytest.fixture(scope='session')
def session_redshift_dataset_cluster(
    client5, group5, user5, session_cross_acc_env_1, org1, session_connection_cluster_data_user, session_id
):
    dataset = None
    try:
        dataset = import_redshift_dataset(
            client=client5,
            label='session_redshift_cluster_dataset1',
            org_uri=org1.organizationUri,
            env_uri=session_cross_acc_env_1.environmentUri,
            description='Used for integration test',
            tags=[session_id],
            owner=user5.username,
            group_uri=group5,
            confidentiality='Secret',
            auto_approval_enabled=False,
            connection_uri=session_connection_cluster_data_user.connectionUri,
            schema=REDSHIFT_SCHEMA,
            tables=[],
        )
        yield dataset
    finally:
        if dataset:
            delete_redshift_dataset(client=client5, dataset_uri=dataset.datasetUri)


@pytest.fixture(scope='session')
def session_redshift_dataset_cluster_table(client5, session_redshift_dataset_cluster):
    add_redshift_dataset_tables(
        client=client5, dataset_uri=session_redshift_dataset_cluster.datasetUri, tables=[REDSHIFT_TABLE1]
    )
    tables = list_redshift_dataset_tables(
        client=client5, dataset_uri=session_redshift_dataset_cluster.datasetUri, term=REDSHIFT_TABLE1
    )
    yield tables.nodes[0]
