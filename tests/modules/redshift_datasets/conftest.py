import os
import pytest
import boto3
from dataall.base.context import set_context, dispose_context, RequestContext

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService
from dataall.modules.redshift_datasets.aws.redshift import RedshiftClient
from dataall.modules.redshift_datasets.aws.redshift_serverless import RedshiftServerlessClient
from dataall.modules.redshift_datasets.aws.redshift_data import RedshiftDataClient

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
        return {
            'ClusterIdentifier': 'cluster_id_1',
            'ClusterStatus': 'available',
            'Encrypted': True,
            'KmsKeyId': 'some-key-id',
        }


class MockRedshiftServerlessClient:
    def get_namespace_by_id(self, *args, **kwargs):
        return {'namespaceId': 'XXXXXXXXXXXXXX', 'namespaceName': 'namespace_name_1', 'KmsKeyId': 'AWS_OWNED_KMS_KEY'}

    def list_workgroups_in_namespace(self, *args, **kwargs):
        return [
            {
                'workgroupName': 'workgroup_name_1',
                'workgroupArn': 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1',
            }
        ]

    def get_workgroup_arn(self, *args, **kwargs):
        return 'arn:aws:redshift-serverless:eu-west-1:XXXXXXXXXXXXXX:workgroup/workgroup_name_1'


@pytest.fixture(scope='module', autouse=True)
def patch_sts_remote_session(module_mocker):
    module_mocker.patch(
        'dataall.base.aws.sts.SessionHelper.remote_session',
        return_value=boto3.Session(),
    )


@pytest.fixture(scope='function')
def patch_redshift(mocker):
    # autospec=True ensures methods called in the MockClient correspond to real client methods
    mocker.patch.object(
        RedshiftClient,
        '__new__',
        return_value=MockRedshiftClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftDataClient,
        '__new__',
        return_value=MockRedshiftDataClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftServerlessClient,
        '__new__',
        return_value=MockRedshiftServerlessClient(),
        autospec=True,
    )
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.kms_redshift.KmsClient.describe_kms_key',
        return_value={'KeyManager': 'AWS'},
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


@pytest.fixture(scope='function')
def connection1_serverless(db, user, group, env_fixture, mocker):
    # autospec=True ensures methods called in the MockClient correspond to real client methods
    mocker.patch.object(
        RedshiftClient,
        '__new__',
        return_value=MockRedshiftClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftDataClient,
        '__new__',
        return_value=MockRedshiftDataClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftServerlessClient,
        '__new__',
        return_value=MockRedshiftServerlessClient(),
        autospec=True,
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def connection2_cluster(db, user, group, env_fixture, mocker):
    # autospec=True ensures methods called in the MockClient correspond to real client methods
    mocker.patch.object(
        RedshiftClient,
        '__new__',
        return_value=MockRedshiftClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftDataClient,
        '__new__',
        return_value=MockRedshiftDataClient(),
        autospec=True,
    )
    mocker.patch.object(
        RedshiftServerlessClient,
        '__new__',
        return_value=MockRedshiftServerlessClient(),
        autospec=True,
    )
    mocker.patch(
        'dataall.modules.redshift_datasets.aws.kms_redshift.KmsClient.describe_kms_key',
        return_value={'KeyManager': 'AWS'},
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def imported_redshift_dataset_1_no_tables(db, user, group, env_fixture, connection1_serverless):
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.delete_redshift_dataset(uri=dataset.datasetUri)
    dispose_context()


@pytest.fixture(scope='function')
def imported_redshift_dataset_2_with_tables(db, user, group, env_fixture, connection1_serverless):
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
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.delete_redshift_dataset(uri=dataset.datasetUri)
    dispose_context()


@pytest.fixture(scope='function')
def imported_dataset_2_table_1(db, user, group, env_fixture, imported_redshift_dataset_2_with_tables):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_2_with_tables.datasetUri, filter={'term': 'table1'}
    )
    dispose_context()
    yield tables['nodes'][0]
