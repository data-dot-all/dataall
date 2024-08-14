"""
Testing LF manager class methods invoked in same account and cross account LF share processors.
Remarks

"""

from unittest.mock import MagicMock

import boto3
import pytest

from typing import Callable

from dataall.core.groups.db.group_models import Group
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.shares_base.services.shares_enums import ShareItemStatus
from dataall.modules.shares_base.db.share_object_models import ShareObject, ShareObjectItem, ShareObjectItemDataFilter
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, S3Dataset
from dataall.modules.s3_datasets_shares.services.s3_share_alarm_service import S3ShareAlarmService
from dataall.modules.s3_datasets_shares.services.share_processors.glue_table_share_processor import (
    ProcessLakeFormationShare,
)
from dataall.modules.s3_datasets_shares.services.share_managers.lf_share_manager import LFShareManager
from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.base.db import exceptions

SOURCE_ENV_ACCOUNT = '1' * 12
SOURCE_ENV_ROLE_NAME = 'dataall-ProducerEnvironment-i6v1v1c2'


TARGET_ACCOUNT_ENV = '2' * 12
TARGET_ACCOUNT_ENV_ROLE_NAME = 'dataall-ConsumersEnvironment-r71ucp4m'


@pytest.fixture(scope='module')
def source_environment(env: Callable, org_fixture: Organization, group: Group) -> Environment:
    yield env(
        org=org_fixture,
        account=SOURCE_ENV_ACCOUNT,
        envname='source_environment',
        owner=group.owner,
        group=group.name,
        role=SOURCE_ENV_ROLE_NAME,
    )


@pytest.fixture(scope='module')
def source_environment_group(environment_group: Callable, source_environment: Environment, group: Group):
    source_environment_group = environment_group(source_environment, group.name)
    yield source_environment_group


@pytest.fixture(scope='module')
def target_environment(env: Callable, org_fixture: Organization, group2: Group) -> Environment:
    yield env(
        org=org_fixture,
        account=TARGET_ACCOUNT_ENV,
        envname='target_environment',
        owner=group2.owner,
        group=group2.name,
        role=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )


@pytest.fixture(scope='module')
def target_environment_group(
    environment_group: Callable, target_environment: Environment, group2: Group
) -> EnvironmentGroup:
    yield environment_group(environment=target_environment, group=group2.name)


@pytest.fixture(scope='module')
def dataset1(create_dataset: Callable, org_fixture: Organization, source_environment: Environment) -> S3Dataset:
    yield create_dataset(organization=org_fixture, environment=source_environment, label='dataset1')


@pytest.fixture(scope='module')
def table1(table: Callable, dataset1: S3Dataset) -> DatasetTable:
    yield table(dataset=dataset1, label='table1')


@pytest.fixture(scope='module')
def table2(table: Callable, dataset1: S3Dataset) -> DatasetTable:
    yield table(dataset=dataset1, label='table2')


@pytest.fixture(scope='module')
def share(
    share: Callable, dataset1: S3Dataset, target_environment: Environment, target_environment_group: EnvironmentGroup
) -> ShareObject:
    yield share(dataset=dataset1, environment=target_environment, env_group=target_environment_group)


@pytest.fixture(scope='module')
def share_item(share_item_table: Callable, share: ShareObject, table1: DatasetTable) -> ShareObjectItem:
    yield share_item_table(share=share, table=table1, status=ShareItemStatus.Share_Approved.value)


@pytest.fixture(scope='module')
def table_data_filter_fixture(db, table1, table_column_data_filter, group, user):
    yield table_column_data_filter(table=table1, name='datafilter1', filterType='COLUMN')


@pytest.fixture(scope='module')
def share_item_data_filter(
    share_item_table_data_filter: Callable, table1: DatasetTable, table_data_filter_fixture
) -> ShareObjectItemDataFilter:
    share_item_data_filter = share_item_table_data_filter(table=table1, table_data_filter=table_data_filter_fixture)
    yield share_item_data_filter


@pytest.fixture(scope='module')
def share_item_with_filters(
    share_item_table: Callable,
    share: ShareObject,
    table1: DatasetTable,
    share_item_data_filter: ShareObjectItemDataFilter,
) -> ShareObjectItem:
    yield share_item_table(
        share=share,
        table=table1,
        status=ShareItemStatus.Share_Approved.value,
        attachedDataFilterUri=share_item_data_filter.attachedDataFilterUri,
    )


@pytest.fixture(scope='module')
def share_data(
    share, dataset1, source_environment, target_environment, source_environment_group, target_environment_group
):
    yield ShareData(
        share=share,
        dataset=dataset1,
        source_environment=source_environment,
        target_environment=target_environment,
        source_env_group=source_environment_group,
        env_group=target_environment_group,
    )


@pytest.fixture(scope='function')
def manager_with_mocked_clients(
    db,
    table1,
    share_data,
    mocker,
    mock_glue_client,
):
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.remote_session',
        return_value=boto3.Session(),
    )
    mocker.patch(
        'dataall.base.aws.iam.IAM.get_role_arn_by_name',
        side_effect=lambda account_id, region, role_name: f'arn:aws:iam::{account_id}:role/{role_name}',
    )
    mock_glue_client().get_glue_database.return_value = False

    mock_glue_client().get_source_catalog.return_value = None

    with db.scoped_session() as session:
        manager = LFShareManager(session=session, share_data=share_data, tables=[table1])
        lf_mock_client = MagicMock()

        mocker.patch.object(
            manager,
            'lf_client_in_target',
            lf_mock_client,
        )
        mocker.patch.object(manager, 'lf_client_in_source', lf_mock_client)
        glue_mock_client = MagicMock()

        mocker.patch.object(manager, 'glue_client_in_target', glue_mock_client)

        mocker.patch.object(manager, 'glue_client_in_source', glue_mock_client)

    yield manager, lf_mock_client, glue_mock_client, mock_glue_client


@pytest.fixture(scope='function')
def mock_glue_client(mocker):
    mock_client = MagicMock()
    mocker.patch('dataall.modules.s3_datasets_shares.services.share_managers.lf_share_manager.GlueClient', mock_client)
    yield mock_client


def test_get_share_principals(
    mocker,
    manager_with_mocked_clients,
    source_environment: Environment,
    target_environment: Environment,
    share: ShareObject,
):
    # Given a dataset and its share, build db_share name
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    get_iam_role_arn_mock = mocker.patch(
        'dataall.base.aws.iam.IAM.get_role_arn_by_name',
        side_effect=lambda account_id, region, role_name: f'arn:aws:iam::{account_id}:role/{role_name}',
    )

    # Then, it should return
    assert manager.get_share_principals() == [
        f'arn:aws:iam::{target_environment.AwsAccountId}:role/{share.principalRoleName}'
    ]
    get_iam_role_arn_mock.assert_called_once()


def test_build_shared_db_name(manager_with_mocked_clients, dataset1: S3Dataset):
    # Given a new share, build db_share name
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # Then
    assert manager.build_shared_db_name() == f'{dataset1.GlueDatabaseName[:247]}_shared'


def test_check_table_exists_in_source_database(
    manager_with_mocked_clients, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = True
    # When
    manager.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_check_table_exists_in_source_database_exception(
    manager_with_mocked_clients, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = False
    # When
    with pytest.raises(Exception) as exception:
        manager.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)
    assert 'ExceptionInfo' in str(exception)


def test_check_resource_link_table_exists_in_target_database_true(manager_with_mocked_clients, table1: DatasetTable):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = True
    # When
    response = manager.check_resource_link_table_exists_in_target_database(resource_link_name=table1.GlueTableName)
    # Then
    assert response == True
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_check_resource_link_table_exists_in_target_database_false(
    manager_with_mocked_clients,
    table1: DatasetTable,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = False
    # Then
    assert manager.check_resource_link_table_exists_in_target_database(resource_link_name=table1.GlueTableName) == False
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_revoke_iam_allowed_principals_from_table(
    manager_with_mocked_clients, table1: DatasetTable, source_environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.revoke_permissions_from_table.return_value = True
    # Then
    assert manager.revoke_iam_allowed_principals_from_table(table1) == True
    lf_client.revoke_permissions_from_table.assert_called_once()
    lf_client.revoke_permissions_from_table.assert_called_with(
        principals=['EVERYONE'],
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['ALL'],
    )


def test_grant_pivot_role_all_database_permissions_to_source_database(
    manager_with_mocked_clients, dataset1: S3Dataset, source_environment: Environment, mocker
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.grant_permissions_to_database.return_value = True
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # Then
    assert manager.grant_pivot_role_all_database_permissions_to_source_database() == True
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=dataset1.GlueDatabaseName,
        permissions=['ALL'],
    )


def test_check_if_exists_and_create_shared_database_in_target(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.create_database.return_value = True
    # When
    manager.check_if_exists_and_create_shared_database_in_target()
    # Then
    glue_client.create_database.assert_called_once()
    glue_client.create_database.assert_called_with(location=f's3://{dataset1.S3BucketName}')


def test_grant_pivot_role_all_database_permissions_to_shared_database(
    manager_with_mocked_clients, dataset1: S3Dataset, mocker
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    manager.grant_pivot_role_all_database_permissions_to_shared_database()
    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['ALL'],
    )


def test_grant_principals_database_permissions_to_shared_database(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.grant_principals_database_permissions_to_shared_database()
    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=manager.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_grant_principals_permissions_to_source_table(
    manager_with_mocked_clients,
    target_environment: Environment,
    source_environment: Environment,
    table1: DatasetTable,
    share_item: ShareObjectItem,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.grant_principals_permissions_to_source_table(table1, share_item)
    # Then
    lf_client.grant_permissions_to_table_with_columns.assert_called_once()
    lf_client.grant_permissions_to_table_with_columns.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_check_if_exists_and_create_resource_link_table_in_shared_database_false(
    manager_with_mocked_clients, table1: DatasetTable, source_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = False
    glue_client.create_resource_link.return_value = True

    # When
    manager.check_if_exists_and_create_resource_link_table_in_shared_database(table1, table1.GlueTableName)

    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.create_resource_link.assert_called_once()
    glue_client.create_resource_link.assert_called_with(
        resource_link_name=table1.GlueTableName,
        database=table1.GlueDatabaseName,
        table=table1,
        catalog_id=source_environment.AwsAccountId,
    )


def test_check_if_exists_and_create_resource_link_table_in_shared_database_true(
    manager_with_mocked_clients, table1: DatasetTable
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = True
    glue_client.create_resource_link.return_value = True

    # When
    manager.check_if_exists_and_create_resource_link_table_in_shared_database(table1, table1.GlueTableName)

    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.create_resource_link.assert_not_called()


def test_grant_principals_permissions_to_resource_link_table(
    manager_with_mocked_clients, table1: DatasetTable, target_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.grant_principals_permissions_to_resource_link_table(table1.GlueTableName)
    # Then
    lf_client.grant_permissions_to_table.assert_called_once()
    lf_client.grant_permissions_to_table.assert_called_with(
        principals=manager.principals,
        database_name=manager.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_grant_pivot_role_drop_permissions_to_resource_link_table(
    manager_with_mocked_clients, table1: DatasetTable, target_environment: Environment, mocker
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    manager.grant_pivot_role_drop_permissions_to_resource_link_table(table1.GlueTableName)
    # Then
    lf_client.grant_permissions_to_table.assert_called_once()
    lf_client.grant_permissions_to_table.assert_called_with(
        principals=['arn:role'],
        database_name=manager.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DROP'],
    )


def test_check_pivot_role_permissions_to_source_database(manager_with_mocked_clients, dataset1: S3Dataset, mocker):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_database.return_value = True
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    manager.check_pivot_role_permissions_to_source_database()
    # Then
    assert len(manager.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=dataset1.GlueDatabaseName,
        permissions=['ALL'],
    )


def test_check_shared_database_in_target(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.get_glue_database.return_value = True
    # When
    manager.check_shared_database_in_target()
    # Then
    glue_client.get_glue_database.assert_called_once()
    assert len(manager.db_level_errors) == 0


def test_check_shared_database_in_target_failed(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.get_glue_database.return_value = False
    # When
    manager.check_shared_database_in_target()
    # Then
    assert len(manager.db_level_errors) == 1


def test_check_pivot_role_permissions_to_shared_database(manager_with_mocked_clients, dataset1: S3Dataset, mocker):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    lf_client.check_permissions_to_database.return_value = True
    # When
    manager.check_pivot_role_permissions_to_shared_database()
    # Then
    assert len(manager.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['ALL'],
    )


def test_check_principals_permissions_to_shared_database(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_database.return_value = True
    # When
    manager.check_principals_permissions_to_shared_database()
    # Then
    assert len(manager.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=manager.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_check_principals_permissions_to_shared_database_failed(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_database.return_value = False
    # When
    manager.check_principals_permissions_to_shared_database()
    # Then
    assert len(manager.db_level_errors) == 1


def test_verify_table_exists_in_source_database(
    manager_with_mocked_clients, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = True
    # When
    manager.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    assert len(manager.tbl_level_errors) == 0
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_verify_table_exists_in_source_database_failed(
    manager_with_mocked_clients, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = False
    # When
    manager.verify_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    assert len(manager.tbl_level_errors) == 1


def test_check_target_principals_permissions_to_source_table(
    manager_with_mocked_clients,
    target_environment: Environment,
    source_environment: Environment,
    table1: DatasetTable,
    share_item: ShareObjectItem,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_table_with_columns.return_value = True
    # When
    manager.check_target_principals_permissions_to_source_table(table1, share_item)
    # Then
    assert len(manager.tbl_level_errors) == 0
    lf_client.check_permissions_to_table_with_columns.assert_called_once()
    lf_client.check_permissions_to_table_with_columns.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_check_target_principals_permissions_to_source_table_data_filters(
    manager_with_mocked_clients,
    target_environment: Environment,
    source_environment: Environment,
    table1: DatasetTable,
    share_item_with_filters: ShareObjectItem,
    share_item_data_filter: ShareObjectItemDataFilter,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_table_with_filters.return_value = True
    # When
    manager.check_target_principals_permissions_to_source_table(table1, share_item, share_item_data_filter)
    # Then
    assert len(manager.tbl_level_errors) == 0
    lf_client.check_permissions_to_table_with_filters.assert_called_once()
    lf_client.check_permissions_to_table_with_filters.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['SELECT'],
        data_filters=share_item_data_filter.dataFilterNames,
    )


def test_grant_principals_permissions_to_source_table_data_filters(
    manager_with_mocked_clients,
    target_environment: Environment,
    source_environment: Environment,
    table1: DatasetTable,
    share_item_with_filters: ShareObjectItem,
    share_item_data_filter: ShareObjectItemDataFilter,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.grant_principals_permissions_to_source_table(table1, share_item, share_item_data_filter)
    # Then
    lf_client.grant_permissions_to_table_with_filters.assert_called_once()
    lf_client.grant_permissions_to_table_with_filters.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['SELECT'],
        data_filters=share_item_data_filter.dataFilterNames,
    )


def test_revoke_principals_permissions_to_table_in_source_data_filters(
    manager_with_mocked_clients,
    table1: DatasetTable,
    source_environment: Environment,
    share_item_with_filters: ShareObjectItem,
    share_item_data_filter: ShareObjectItemDataFilter,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.revoke_principals_permissions_to_table_in_source(
        table=table1, share_item=share_item, share_item_filter=share_item_data_filter
    )
    # Then
    lf_client.revoke_permissions_to_table_with_filters.assert_called_once()
    lf_client.revoke_permissions_to_table_with_filters.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['SELECT'],
        data_filters=share_item_data_filter.dataFilterNames,
    )


def test_check_target_principals_permissions_to_source_table_failed(
    manager_with_mocked_clients,
    target_environment: Environment,
    source_environment: Environment,
    table1: DatasetTable,
    share_item: ShareObjectItem,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_table_with_columns.return_value = False
    # When
    manager.check_target_principals_permissions_to_source_table(table1, share_item)
    # Then
    assert len(manager.tbl_level_errors) == 1


def test_verify_resource_link_table_exists_in_target_database(
    manager_with_mocked_clients, table1: DatasetTable, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = True
    # When
    manager.verify_resource_link_table_exists_in_target_database(resource_link_name=table1.GlueTableName)
    # Then
    assert len(manager.tbl_level_errors) == 0
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_verify_resource_link_table_exists_in_target_database_failed(
    manager_with_mocked_clients, table1: DatasetTable, mock_glue_client
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    glue_client.table_exists.return_value = False
    # When
    manager.verify_resource_link_table_exists_in_target_database(resource_link_name=table1.GlueTableName)
    # Then
    assert len(manager.tbl_level_errors) == 1


def test_check_principals_permissions_to_resource_link_table(
    manager_with_mocked_clients, table1: DatasetTable, target_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_table_with_columns.return_value = True
    # When
    manager.check_principals_permissions_to_resource_link_table(table1.GlueTableName)
    # Then
    assert len(manager.tbl_level_errors) == 0
    lf_client.check_permissions_to_table.assert_called_once()
    lf_client.check_permissions_to_table.assert_called_with(
        principals=manager.principals,
        database_name=manager.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_check_principals_permissions_to_resource_link_table_failed(
    manager_with_mocked_clients, table1: DatasetTable, source_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    lf_client.check_permissions_to_table.return_value = False
    # When
    manager.check_principals_permissions_to_resource_link_table(table1.GlueTableName)
    # Then
    assert len(manager.tbl_level_errors) == 1


def test_revoke_principals_permissions_to_resource_link_table(
    manager_with_mocked_clients, table1: DatasetTable, target_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.revoke_principals_permissions_to_resource_link_table(resource_link_name=table1.GlueTableName)
    # Then
    lf_client.revoke_permissions_from_table.assert_called_once()
    lf_client.revoke_permissions_from_table.assert_called_with(
        principals=manager.principals,
        database_name=manager.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_revoke_principals_permissions_to_table_in_source(
    manager_with_mocked_clients, table1: DatasetTable, source_environment: Environment, share_item: ShareObjectItem
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.revoke_principals_permissions_to_table_in_source(table=table1, share_item=share_item)
    # Then
    lf_client.revoke_permissions_from_table_with_columns.assert_called_once()
    lf_client.revoke_permissions_from_table_with_columns.assert_called_with(
        principals=manager.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_delete_resource_link_table_in_shared_database_true(manager_with_mocked_clients, table2: DatasetTable):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.delete_resource_link_table_in_shared_database(resource_link_name=table2.GlueTableName)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.delete_table.assert_called_once()


def test_revoke_principals_database_permissions_to_shared_database(manager_with_mocked_clients, dataset1: S3Dataset):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.revoke_principals_database_permissions_to_shared_database()
    # Then
    lf_client.revoke_permissions_to_database.assert_called_once()
    lf_client.revoke_permissions_to_database.assert_called_with(
        principals=manager.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_delete_shared_database_in_target(
    manager_with_mocked_clients,
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients
    # When
    manager.delete_shared_database_in_target()
    # Then
    glue_client.delete_database.assert_called_once()


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists(
    db,
    table1,
    source_environment,
    share_data,
    mocker,
    mock_glue_client,
):
    # Mock glue and sts calls to create a LF processor
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.remote_session',
        return_value=boto3.Session(),
    )
    mocker.patch(
        'dataall.base.aws.iam.IAM.get_role_arn_by_name',
        side_effect=lambda account_id, region, role_name: f'arn:aws:iam::{account_id}:role/{role_name}',
    )
    mock_glue_client().get_glue_database.return_value = False

    mock_glue_client().get_source_catalog.return_value = {
        'account_id': '12129101212',
        'database_name': 'catalog_db',
        'region': 'us-east-1',
    }

    mock_glue_client().get_database_tags.return_value = {'owner_account_id': source_environment.AwsAccountId}

    mocker.patch('dataall.base.aws.sts.SessionHelper.is_assumable_pivot_role', return_value=True)

    # when
    with db.scoped_session() as session:
        # Check if the catalog account exists
        manager = LFShareManager(session=session, share_data=share_data, tables=[table1])
        assert manager.check_catalog_account_exists_and_verify() == True
        # Then
        # Check the source account id. source account database and region to check if it is updated
        assert manager.source_account_id == '12129101212'
        assert manager.source_database_name == 'catalog_db'
        assert manager.source_account_region == 'us-east-1'

        # Check the shared database
        assert manager.shared_db_name == 'catalog_db' + '_shared'


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists_and_pivot_role_not_assumable(
    manager_with_mocked_clients,
    table1: DatasetTable,
    source_environment: Environment,
    target_environment: Environment,
    mocker,
):
    # Given
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients

    # Override the mocks to check catalog account details
    mock_glue_client().get_source_catalog.return_value = {
        'account_id': '12129101212',
        'database_name': 'catalog_db',
        'region': 'us-east-1',
    }

    mock_glue_client().get_database_tags.return_value = {'owner_account_id': source_environment.AwsAccountId}

    mock_glue_client().get_glue_database.return_value = False

    mocker.patch('dataall.base.aws.sts.SessionHelper.is_assumable_pivot_role', return_value=False)

    # When
    with pytest.raises(Exception) as exception:
        manager._verify_catalog_ownership('12129101212', 'us-east-1', 'catalog_db')

    # Then
    assert 'Pivot role is not assumable' in str(exception)
    assert manager.check_catalog_account_exists_and_verify() is None


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists_and_tag_doesnt_exists(
    manager_with_mocked_clients,
    table1: DatasetTable,
    source_environment: Environment,
    target_environment: Environment,
    mocker,
):
    # Given
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients

    # Override the mocks to check catalog account details
    mock_glue_client().get_source_catalog.return_value = {
        'account_id': '12129101212',
        'database_name': 'catalog_db',
        'region': 'us-east-1',
    }

    mock_glue_client().get_database_tags.return_value = {'owner_account_id': 'NotTheSourceAccountID'}

    mock_glue_client().get_glue_database.return_value = False

    mocker.patch('dataall.base.aws.sts.SessionHelper.is_assumable_pivot_role', return_value=True)

    # when
    with pytest.raises(Exception) as exception:
        manager._validate_catalog_ownership_tag('12129101212', 'us-east-1', 'catalog_db')

    # then
    assert manager.check_catalog_account_exists_and_verify() is None
    assert 'owner_account_id tag does not exist or does not matches the source account id' in str(exception)


def test_check_catalog_account_exists_and_update_processor_with_catalog_doesnt_exists(
    manager_with_mocked_clients, table1: DatasetTable, source_environment: Environment, target_environment: Environment
):
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients

    # When
    assert manager.check_catalog_account_exists_and_verify() == False

    # Then
    # Check the source account id. source account database and region to check if it is updated
    assert manager.source_account_id == source_environment.AwsAccountId
    assert manager.source_database_name == manager.dataset.GlueDatabaseName
    assert manager.source_account_region == source_environment.region

    # Check the shared database
    assert manager.shared_db_name == manager.dataset.GlueDatabaseName + '_shared'


def test_handle_share_failure(manager_with_mocked_clients, table1: DatasetTable, mocker):
    # Given
    alarm_service_mock = mocker.patch.object(S3ShareAlarmService, 'trigger_table_sharing_failure_alarm')
    error = Exception()
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients

    # When
    manager.handle_share_failure(table1, error)

    # Then
    alarm_service_mock.assert_called_once()


def test_handle_revoke_failure(
    manager_with_mocked_clients,
    table1: DatasetTable,
    mocker,
):
    # Given
    alarm_service_mock = mocker.patch.object(S3ShareAlarmService, 'trigger_revoke_table_sharing_failure_alarm')
    error = Exception()
    manager, lf_client, glue_client, mock_glue_client = manager_with_mocked_clients

    # When
    manager.handle_revoke_failure(table1, error)

    # Then
    alarm_service_mock.assert_called_once()
