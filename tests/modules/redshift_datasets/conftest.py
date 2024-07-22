import pytest

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService

from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService


class MockRedshiftDataClient:
    def get_redshift_connection_database(self, database):
        return True

    def list_redshift_schemas(self, schema):
        return [schema]

    def list_redshift_tables(self):
        return [
            {'name': 'table1', 'type': 'TABLE'},
            {'name': 'table2', 'type': 'TABLE'},
            {'name': 'table3', 'type': 'TABLE'},
            {'name': 'table4', 'type': 'TABLE'},
        ]

    def list_redshift_table_columns(self):
        return [
            {'name': 'column1', 'type': 'VARCHAR', 'nullable': True},
            {'name': 'column2', 'type': 'INTEGER', 'nullable': False},
            {'name': 'column3', 'type': 'DOUBLE', 'nullable': True},
            {'name': 'column4', 'type': 'BOOLEAN', 'nullable': False},
        ]


class MockRedshiftClient:
    def describe_cluster(self):
        return {'ClusterIdentifier': 'cluster_id_1', 'ClusterStatus': 'available'}


class MockRedshiftServerlessClient:
    def get_namespace_by_id(self):
        return {'namespaceId': 'XXXXXXXXXXXXXX', 'namespaceName': 'namespace_name_1'}

    def list_workgroups_in_namespace(self):
        return [
            {
                'workgroupName': 'workgroup_name_1',
                'workgroupArn': 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1',
            }
        ]

    def get_workgroup_arn(self):
        return 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1'


@pytest.fixture(scope='function')
def patch_redshift_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_client',
        return_value=MockRedshiftClient(),
    )


@pytest.fixture(scope='function')
def patch_redshift_data_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_data_client',
        return_value=MockRedshiftDataClient(),
    )


@pytest.fixture(scope='function')
def patch_redshift_serverless_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.redshift_datasets.services.redshift_connection_service.redshift_serverless_client',
        return_value=MockRedshiftServerlessClient(),
    )


@pytest.fixture(scope='function')
def patch_redshift(patch_redshift_client, patch_redshift_data_client, patch_redshift_serverless_client):
    yield patch_redshift_client, patch_redshift_data_client, patch_redshift_serverless_client


@pytest.fixture(scope='session')
def connection1_serverless(env1, group1, patch_redshift):
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env1.environmentUri,
        admin_group=group1,
        data={
            'connectionName': 'connection1',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'XXXXXXXXXXXXXX',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        },
    )
    yield connection


@pytest.fixture(scope='session')
def connection2_cluster(env1, group1, patch_redshift):
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env1.environmentUri,
        admin_group=group1,
        data={
            'connectionName': 'connection2',
            'redshiftType': 'cluster',
            'clusterId': 'XXXXXXXXXXXXXX',
            'nameSpaceId': None,
            'workgroup': None,
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        },
    )
    yield connection
