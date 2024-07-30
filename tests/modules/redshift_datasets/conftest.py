import os
import pytest

from dataall.base.context import set_context, dispose_context, RequestContext

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService

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
    # Mocking connection service
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
    # Mocking dataset service
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_dataset_service.redshift_data_client',
        return_value=MockRedshiftDataClient(),
    )


@pytest.fixture(scope='function')
def api_context_1(db, user, group):
    yield set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    dispose_context()


@pytest.fixture(scope='function')
def api_context_2(db, user2, group2):
    yield set_context(
        RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username)
    )
    dispose_context()


@pytest.fixture(scope='module')
def connection1_serverless(db, user, group, env_fixture, module_mocker):
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
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
def connection2_cluster(db, user, group, env_fixture, module_mocker):
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
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


@pytest.fixture(scope='module')
def imported_redshift_dataset_1_no_tables(db, user, group, env_fixture, connection1_serverless, module_mocker):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    dataset = RedshiftDatasetService.import_redshift_dataset(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'label': 'imported_redshift_dataset_1',
            'SamlAdminGroupName': group.name,
            'connectionUri': connection1_serverless.connectionUri,
            'schema': 'public',
        },
    )
    dispose_context()
    yield dataset


@pytest.fixture(scope='module')
def imported_redshift_dataset_2_with_tables(db, user, group, env_fixture, connection1_serverless, module_mocker):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    dataset = RedshiftDatasetService.import_redshift_dataset(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'label': 'imported_redshift_dataset_2',
            'SamlAdminGroupName': group.name,
            'connectionUri': connection1_serverless.connectionUri,
            'schema': 'public',
            'tables': ['table1', 'table2'],
        },
    )
    dispose_context()
    yield dataset


@pytest.fixture(scope='module')
def imported_dataset_2_table_1(db, user, group, env_fixture, imported_redshift_dataset_2_with_tables):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_2_with_tables.datasetUri, filter={'term': 'table1'}
    )
    dispose_context()
    yield tables['nodes'][0]
