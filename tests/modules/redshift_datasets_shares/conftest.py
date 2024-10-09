import pytest
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.modules.shares_base.services.share_object_service import ShareObjectService
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.shares_enums import ShareItemStatus, ShareObjectDataPermission
from dataall.modules.shares_base.services.share_item_service import ShareItemService
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
from dataall.modules.redshift_datasets_shares.services.redshift_table_share_processor import ProcessRedshiftShare
from dataall.modules.redshift_datasets_shares.services.redshift_shares_enums import RedshiftDatashareStatus


@pytest.fixture(scope='function')
def mock_redshift_data_shares(mocker):
    redshiftShareDataClient = mocker.patch(
        'dataall.modules.redshift_datasets_shares.aws.redshift_data.RedshiftShareDataClient', autospec=True
    )
    redshiftShareDataClient.return_value.check_datashare_exists.return_value = True
    redshiftShareDataClient.return_value.check_schema_in_datashare.return_value = True
    redshiftShareDataClient.return_value.check_table_in_datashare.return_value = True
    redshiftShareDataClient.return_value.check_consumer_permissions_to_datashare.return_value = True
    redshiftShareDataClient.return_value.check_database_exists.return_value = True
    redshiftShareDataClient.return_value.check_role_permissions_in_database.return_value = True
    redshiftShareDataClient.return_value.check_schema_exists.return_value = True
    redshiftShareDataClient.return_value.check_role_permissions_in_schema.return_value = True
    redshiftShareDataClient.return_value.check_redshift_role_in_namespace.return_value = True

    yield redshiftShareDataClient


@pytest.fixture(scope='function')
def mock_redshift_shares(mocker):
    redshiftClient = mocker.patch(
        'dataall.modules.redshift_datasets_shares.aws.redshift.RedshiftShareClient', autospec=True
    )
    redshiftClient.return_value.get_datashare_status.return_value = RedshiftDatashareStatus.Active.value
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
def api_context_3(db, user3, group3):
    yield set_context(
        RequestContext(db_engine=db, username=user3.username, groups=[group3.name], user_id=user3.username)
    )
    dispose_context()


@pytest.fixture(scope='module')
def env_fixture_2(env, environment_group, org_fixture, user2, group2, tenant, env_params):
    env2 = env(org_fixture, 'dev', 'bob', 'testadmins', '2222222222', parameters=env_params)
    environment_group(env2, group2.name)
    yield env2


@pytest.fixture(scope='module')
def env_fixture_same_1(env, environment_group, org_fixture, user2, group2, tenant, env_params):
    env2 = env(org_fixture, 'dev', 'bob', 'testadmins', '111111111111', parameters=env_params)
    environment_group(env2, group2.name)
    yield env2


@pytest.fixture(scope='function')
def source_connection_data_user(db, user, group, env_fixture, mock_redshift_serverless, mock_redshift_data):
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
            'connectionType': 'DATA_USER',
        },
    )
    dispose_context()
    yield connection
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def source_connection_admin(db, user, group, env_fixture, mock_redshift_serverless, mock_redshift_data):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'connectionName': 'connection1_admin',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'XXXXXXXXXXXXXX',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:111111111111:secret:secret-1',
            'connectionType': 'ADMIN',
        },
    )
    dispose_context()
    yield connection
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def target_connection_data_user(db, user2, group2, env_fixture_2, mock_redshift_serverless, mock_redshift_data):
    """Cross-account connection"""
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture_2.environmentUri,
        admin_group=group2.name,
        data={
            'connectionName': 'connection2',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'YYYYYYYYYYYYYY',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:222222222222:secret:secret-2',
            'connectionType': 'DATA_USER',
        },
    )
    dispose_context()
    yield connection
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def target_connection_admin(db, user2, group2, env_fixture_2, mock_redshift_serverless, mock_redshift_data):
    """Cross-account connection"""
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture_2.environmentUri,
        admin_group=group2.name,
        data={
            'connectionName': 'connection2',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'YYYYYYYYYYYYYY',
            'workgroup': 'workgroup_name_1',
            'database': 'database_1',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:222222222222:secret:secret-2',
            'connectionType': 'ADMIN',
        },
    )
    dispose_context()
    yield connection
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def target_connection_same_account(db, user2, group2, env_fixture_same_1, mock_redshift_serverless, mock_redshift_data):
    """Same account connection"""
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    connection = RedshiftConnectionService.create_redshift_connection(
        uri=env_fixture_same_1.environmentUri,
        admin_group=group2.name,
        data={
            'connectionName': 'connection3',
            'redshiftType': 'serverless',
            'clusterId': None,
            'nameSpaceId': 'ZZZZZZZZZZZZ',
            'workgroup': 'workgroup_name_1',
            'database': 'database_2',
            'redshiftUser': None,
            'secretArn': 'arn:aws:secretsmanager:*:11111111111:secret:secret-3',
            'connectionType': 'ADMIN',
        },
    )
    dispose_context()
    yield connection
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    RedshiftConnectionService.delete_redshift_connection(uri=connection.connectionUri)
    dispose_context()


@pytest.fixture(scope='function')
def dataset_1(db, user, group, env_fixture, source_connection_data_user):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    dataset = RedshiftDatasetService.import_redshift_dataset(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'label': 'dataset_1',
            'SamlAdminGroupName': group.name,
            'connectionUri': source_connection_data_user.connectionUri,
            'schema': 'public',
            'tables': [],
        },
    )
    dispose_context()
    yield dataset
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.delete_redshift_dataset(uri=dataset.datasetUri)
    dispose_context()


@pytest.fixture(scope='function')
def table1(db, user, group, dataset_1):
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    RedshiftDatasetService.add_redshift_dataset_tables(uri=dataset_1.datasetUri, tables=['table1'])
    paginated_tables = RedshiftDatasetService.list_redshift_dataset_tables(uri=dataset_1.datasetUri, filter={})
    dispose_context()
    assert paginated_tables.get('count', 0) == 1
    yield paginated_tables.get('nodes')[0]


@pytest.fixture(scope='function')
def redshift_share_request_cross_account(
    db,
    user2,
    group2,
    env_fixture_2,
    target_connection_admin,
    dataset_1,
    mock_redshift_data_shares,
    source_connection_admin,
):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    share = ShareObjectService.create_share_object(
        uri=env_fixture_2.environmentUri,
        dataset_uri=dataset_1.datasetUri,
        item_type=None,
        item_uri=None,
        group_uri=group2.name,
        principal_id=target_connection_admin.connectionUri,
        principal_role_name='rs_role_1',
        principal_type='Redshift_Role',
        requestPurpose=None,
        attachMissingPolicies=False,
        permissions=[ShareObjectDataPermission.Read.value],
        shareExpirationPeriod=None,
    )
    dispose_context()
    yield share


@pytest.fixture(scope='function')
def redshift_share_request_2_same_account(
    db,
    user2,
    group2,
    env_fixture_same_1,
    target_connection_same_account,
    dataset_1,
    mock_redshift_data_shares,
    source_connection_admin,
):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    share = ShareObjectService.create_share_object(
        uri=env_fixture_same_1.environmentUri,
        dataset_uri=dataset_1.datasetUri,
        item_type=None,
        item_uri=None,
        group_uri=group2.name,
        principal_id=target_connection_same_account.connectionUri,
        principal_role_name='rs_role_1',
        principal_type='Redshift_Role',
        requestPurpose=None,
        attachMissingPolicies=False,
        permissions=[ShareObjectDataPermission.Read.value],
        shareExpirationPeriod=None,
    )
    dispose_context()
    yield share


@pytest.fixture(scope='function')
def redshift_requested_table(db, user2, group2, redshift_share_request_cross_account, table1):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    item = ShareItemService.add_shared_item(
        uri=redshift_share_request_cross_account.shareUri,
        data={'itemType': 'RedshiftTable', 'itemUri': table1.rsTableUri},
    )
    dispose_context()
    yield item
    with db.scoped_session() as session:
        session.delete(item)


@pytest.fixture(scope='function')
def redshift_requested_table_2(db, user2, group2, redshift_share_request_2_same_account, table1):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    item = ShareItemService.add_shared_item(
        uri=redshift_share_request_2_same_account.shareUri,
        data={'itemType': 'RedshiftTable', 'itemUri': table1.rsTableUri},
    )
    dispose_context()
    yield item
    with db.scoped_session() as session:
        session.delete(item)


@pytest.fixture(scope='function')
def approved_share_data_cross_account(
    db,
    user,
    user2,
    group,
    group2,
    redshift_share_request_cross_account,
    redshift_requested_table,
    dataset_1,
    env_fixture,
    env_fixture_2,
    mock_redshift_data_shares,
):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    ShareObjectService.submit_share_object(uri=redshift_share_request_cross_account.shareUri)
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    ShareObjectService.approve_share_object(uri=redshift_share_request_cross_account.shareUri)
    dispose_context()
    yield ShareData(
        share=redshift_share_request_cross_account,
        dataset=dataset_1,
        source_environment=env_fixture,
        target_environment=env_fixture_2,
        source_env_group=group,
        env_group=group2,
    )


@pytest.fixture(scope='function')
def approved_share_data_same_account(
    db,
    user,
    user2,
    group,
    group2,
    redshift_share_request_2_same_account,
    redshift_requested_table_2,
    dataset_1,
    env_fixture,
    env_fixture_same_1,
    mock_redshift_data_shares,
):
    set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
    ShareObjectService.submit_share_object(uri=redshift_share_request_2_same_account.shareUri)
    set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    ShareObjectService.approve_share_object(uri=redshift_share_request_2_same_account.shareUri)
    dispose_context()
    yield ShareData(
        share=redshift_share_request_2_same_account,
        dataset=dataset_1,
        source_environment=env_fixture,
        target_environment=env_fixture_same_1,
        source_env_group=group,
        env_group=group2,
    )


@pytest.fixture(scope='function')
def shareable_items_1(db, approved_share_data_cross_account):
    with db.scoped_session() as session:
        yield ShareObjectRepository.get_share_data_items_by_type(
            session,
            approved_share_data_cross_account.share,
            RedshiftTable,
            RedshiftTable.rsTableUri,
            status=ShareItemStatus.Share_Approved.value,
        )


@pytest.fixture(scope='function')
def shareable_items_2(db, approved_share_data_same_account):
    with db.scoped_session() as session:
        yield ShareObjectRepository.get_share_data_items_by_type(
            session,
            approved_share_data_same_account.share,
            RedshiftTable,
            RedshiftTable.rsTableUri,
            status=ShareItemStatus.Share_Approved.value,
        )


@pytest.fixture(scope='function')
def redshift_processor_cross_account(db, approved_share_data_cross_account, shareable_items_1):
    with db.scoped_session() as session:
        processor = ProcessRedshiftShare(
            session=session, share_data=approved_share_data_cross_account, shareable_items=shareable_items_1
        )
    yield processor


@pytest.fixture(scope='function')
def redshift_processor_same_account(db, approved_share_data_same_account, shareable_items_2):
    with db.scoped_session() as session:
        processor = ProcessRedshiftShare(
            session=session, share_data=approved_share_data_same_account, shareable_items=shareable_items_2
        )
    yield processor
