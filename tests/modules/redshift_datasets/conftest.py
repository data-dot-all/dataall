import os
import pytest

from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.base.db import get_engine

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService

ENVNAME = os.environ.get('envname', 'pytest')

class MockRedshiftDataClient:
    def get_redshift_connection_database(self, *args, **kwargs):
        return True

    def list_redshift_schemas(self, *args, **kwargs):
        return ['public', 'dev']

    def list_redshift_tables(self, *args, **kwargs):
        return [
            {'name': 'table1', 'type': 'TABLE'},
            {'name': 'table2', 'type': 'TABLE'},
            {'name': 'table3', 'type': 'TABLE'},
            {'name': 'table4', 'type': 'TABLE'},
        ]

    def list_redshift_table_columns(self, *args, **kwargs):
        return [
            {'name': 'column1', 'type': 'VARCHAR', 'nullable': True},
            {'name': 'column2', 'type': 'INTEGER', 'nullable': False},
            {'name': 'column3', 'type': 'DOUBLE', 'nullable': True},
            {'name': 'column4', 'type': 'BOOLEAN', 'nullable': False},
        ]


class MockRedshiftClient:
    def describe_cluster(self, *args, **kwargs):
        return {'ClusterIdentifier': 'cluster_id_1', 'ClusterStatus': 'available'}


class MockRedshiftServerlessClient:
    def get_namespace_by_id(self, *args, **kwargs):
        return {'namespaceId': 'XXXXXXXXXXXXXX', 'namespaceName': 'namespace_name_1'}

    def list_workgroups_in_namespace(self, *args, **kwargs):
        return [
            {
                'workgroupName': 'workgroup_name_1',
                'workgroupArn': 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1',
            }
        ]

    def get_workgroup_arn(self, *args, **kwargs):
        return 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1'


@pytest.fixture(scope='function')
def patch_redshift(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_client',
        return_value=MockRedshiftClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_data_client',
        return_value=MockRedshiftDataClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_serverless_client',
        return_value=MockRedshiftServerlessClient(),
    )

@pytest.fixture(scope='function')
def api_context_1(user, group):
    engine = get_engine(envname=ENVNAME)
    yield set_context(RequestContext(db_engine=engine, username=user.username, groups=[group.name], user_id=user.username))
    dispose_context()

@pytest.fixture(scope='function')
def api_context_2(user2, group2):
    engine = get_engine(envname=ENVNAME)
    yield set_context(RequestContext(db_engine=engine, username=user2.username, groups=[group2.name], user_id=user2.username))
    dispose_context()


@pytest.fixture(scope='module')
def connection1_serverless(user, group, env_fixture,module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_client',
        return_value=MockRedshiftClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_data_client',
        return_value=MockRedshiftDataClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_serverless_client',
        return_value=MockRedshiftServerlessClient(),
    )
    engine = get_engine(envname=ENVNAME)
    set_context(RequestContext(db_engine=engine, username=user.username, groups=[group.name], user_id=user.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection1',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'XXXXXXXXXXXXXX',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-1',
        },
    )
    dispose_context()
    yield connection


@pytest.fixture(scope='module')
def connection2_cluster(user, group, env_fixture, module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_client',
        return_value=MockRedshiftClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_data_client',
        return_value=MockRedshiftDataClient(),
    )
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_serverless_client',
        return_value=MockRedshiftServerlessClient(),
    )
    engine = get_engine(envname=ENVNAME)
    set_context(RequestContext(db_engine=engine, username=user.username, groups=[group.name], user_id=user.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection2',
            'redshiftType': 'cluster',
            'clusterId': 'cluster-id',
            'nameSpaceId': None,
            'workgroup': None,
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-2',
        },
    )
    dispose_context()
    yield connection
