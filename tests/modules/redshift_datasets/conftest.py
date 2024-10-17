import os

import boto3
import pytest
from unittest.mock import MagicMock

from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.core.organizations.services.organization_service import OrganizationService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService
from dataall.modules.redshift_datasets.services.redshift_connection_permissions import REDSHIFT_GRANTABLE_PERMISSIONS

ENVNAME = os.environ.get('envname', 'pytest')


@pytest.fixture(scope='module', autouse=True)
def patch_sts_remote_session(module_mocker):
    module_mocker.patch(
        'dataall.base.aws.sts.SessionHelper.remote_session',
        return_value=boto3.Session(),
    )


@pytest.fixture(scope='function')
def mock_redshift(mocker):
    redshiftClient = mocker.patch('dataall.modules.redshift_datasets.aws.redshift.RedshiftClient', autospec=True)
    redshiftClient.return_value.describe_cluster.return_value = {
        'ClusterIdentifier': 'cluster_id_1',
        'ClusterStatus': 'available',
        'Encrypted': True,
        'KmsKeyId': 'some-key-id',
    }
    redshiftClient.return_value.get_cluster_namespaceId.return_value = 'namespaceId1'
    yield redshiftClient


@pytest.fixture(scope='function')
def mock_redshift_data(mocker):
    redshiftDataClient = mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_data.RedshiftDataClient', autospec=True
    )
    redshiftDataClient.return_value.get_redshift_connection_database.return_value = True
    redshiftDataClient.return_value.list_redshift_schemas.return_value = ['public', 'dev']
    redshiftDataClient.return_value.list_redshift_tables.return_value = [
        {'name': 'table1', 'type': 'TABLE'},
        {'name': 'table2', 'type': 'TABLE'},
        {'name': 'table3', 'type': 'TABLE'},
        {'name': 'table4', 'type': 'TABLE'},
    ]
    redshiftDataClient.return_value.list_redshift_table_columns.return_value = [
        {'name': 'column1', 'type': 'VARCHAR', 'nullable': True},
        {'name': 'column2', 'type': 'INTEGER', 'nullable': False},
        {'name': 'column3', 'type': 'DOUBLE', 'nullable': True},
        {'name': 'column4', 'type': 'BOOLEAN', 'nullable': False},
    ]
    yield redshiftDataClient


@pytest.fixture(scope='function')
def mock_redshift_serverless(mocker):
    redshiftServerlessClient = mocker.patch(
        'dataall.modules.redshift_datasets.aws.redshift_serverless.RedshiftServerlessClient', autospec=True
    )
    redshiftServerlessClient.return_value.get_namespace_by_id.return_value = {
        'namespaceId': 'XXXXXXXXXXXXXX',
        'namespaceName': 'namespace_name_1',
        'KmsKeyId': 'AWS_OWNED_KMS_KEY',
    }
    redshiftServerlessClient.return_value.list_workgroups_in_namespace.return_value = [
        {
            'workgroupName': 'workgroup_name_1',
            'workgroupArn': 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1',
        }
    ]
    redshiftServerlessClient.return_value.get_workgroup_arn.return_value = (
        'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1'
    )
    yield redshiftServerlessClient


@pytest.fixture(scope='function')
def mock_redshift_kms(mocker):
    kmsClient = mocker.patch('dataall.modules.redshift_datasets.aws.kms_redshift.KmsClient', autospec=True)
    kmsClient.return_value.describe_kms_key.return_value = {'KeyManager': 'AWS'}
    yield kmsClient


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


@pytest.fixture(scope='function')
def connection1_serverless(db, user, group, env_fixture, mock_redshift_serverless, mock_redshift_data, api_context_1):
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
            'connectionType': 'DATA_USER',
        },
    )
    yield connection
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def connection2_cluster(
    db, user, group, env_fixture, mock_redshift, mock_redshift_data, mock_redshift_kms, api_context_1
):
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
            'connectionType': 'DATA_USER',
        },
    )
    yield connection
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def connection3_admin(
    db, user, group, env_fixture, mock_redshift, mock_redshift_data, mock_redshift_kms, api_context_1
):
    connection = RedshiftConnectionService.create_redshift_connection(
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
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-3',
            'connectionType': 'ADMIN',
        },
    )
    yield connection
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def invited_group_to_environment(db, user, group, group2, env_fixture, api_context_1, module_mocker):
    module_mocker.patch('dataall.base.aws.iam.IAM', return_value=MagicMock())
    OrganizationService.invite_group(
        uri=env_fixture.organizationUri, data={'groupUri': group2.name, 'permissions': ['LINK_ENVIRONMENT']}
    )
    EnvironmentService.invite_group(
        uri=env_fixture.environmentUri, data={'groupUri': group2.name, 'permissions': ['INVITE_ENVIRONMENT_GROUP']}
    )
    yield group2
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    EnvironmentService.remove_group(uri=env_fixture.environmentUri, group=group2.name)
    OrganizationService.remove_group(uri=env_fixture.organizationUri, group=group2.name)


@pytest.fixture(scope='function')
def connection3_admin_permissions(db, connection3_admin, user, group, invited_group_to_environment, api_context_1):
    RedshiftConnectionService.add_group_permissions(
        uri=connection3_admin.connectionUri,
        group=invited_group_to_environment.name,
        permissions=REDSHIFT_GRANTABLE_PERMISSIONS,
    )
    yield RedshiftConnectionService.list_connection_group_permissions(uri=connection3_admin.connectionUri, filter={})
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_group_permissions(
        uri=connection3_admin.connectionUri, group=invited_group_to_environment.name
    )
    dispose_context()


@pytest.fixture(scope='function')
def imported_redshift_dataset_1_no_tables(db, user, group, env_fixture, connection1_serverless, api_context_1):
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
    yield dataset
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.delete_redshift_dataset(uri=dataset.datasetUri)
    dispose_context()


@pytest.fixture(scope='function')
def imported_redshift_dataset_2_with_tables(
    db, user, group, env_fixture, connection1_serverless, api_context_1, mock_redshift_data
):
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
    yield dataset
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.delete_redshift_dataset(uri=dataset.datasetUri)
    dispose_context()


@pytest.fixture(scope='function')
def imported_dataset_2_table_1(db, user, group, env_fixture, imported_redshift_dataset_2_with_tables, api_context_1):
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_2_with_tables.datasetUri, filter={'term': 'table1'}
    )
    yield tables['nodes'][0]
