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
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import ShareItemStatus
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject, ShareObjectItem
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.dataset_sharing.services.dataset_alarm_service import DatasetAlarmService
from dataall.modules.dataset_sharing.services.share_processors.lakeformation_process_share import (
    ProcessLakeFormationShare,
)
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
def dataset1(create_dataset: Callable, org_fixture: Organization, source_environment: Environment) -> Dataset:
    yield create_dataset(organization=org_fixture, environment=source_environment, label='dataset1')


@pytest.fixture(scope='module')
def table1(table: Callable, dataset1: Dataset) -> DatasetTable:
    yield table(dataset=dataset1, label='table1')


@pytest.fixture(scope='module')
def table2(table: Callable, dataset1: Dataset) -> DatasetTable:
    yield table(dataset=dataset1, label='table2')


@pytest.fixture(scope='module')
def share(
    share: Callable, dataset1: Dataset, target_environment: Environment, target_environment_group: EnvironmentGroup
) -> ShareObject:
    yield share(dataset=dataset1, environment=target_environment, env_group=target_environment_group)


@pytest.fixture(scope='module')
def share_item(share_item_table: Callable, share: ShareObject, table1: DatasetTable) -> ShareObjectItem:
    yield share_item_table(share=share, table=table1, status=ShareItemStatus.Share_Approved.value)


@pytest.fixture(scope='function', autouse=True)
def processor_with_mocks(
    db,
    dataset1,
    share,
    table1,
    table2,
    source_environment,
    target_environment,
    target_environment_group,
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
        processor = ProcessLakeFormationShare(
            session,
            dataset1,
            share,
            [table1],
            source_environment,
            target_environment,
            target_environment_group,
        )
        lf_mock_client = MagicMock()

        mocker.patch.object(
            processor,
            'lf_client_in_target',
            lf_mock_client,
        )
        mocker.patch.object(processor, 'lf_client_in_source', lf_mock_client)
        glue_mock_client = MagicMock()

        mocker.patch.object(processor, 'glue_client_in_target', glue_mock_client)

        mocker.patch.object(processor, 'glue_client_in_source', glue_mock_client)

    yield processor, lf_mock_client, glue_mock_client, mock_glue_client


@pytest.fixture(scope='function')
def mock_glue_client(mocker):
    mock_client = MagicMock()
    mocker.patch('dataall.modules.dataset_sharing.services.share_managers.lf_share_manager.GlueClient', mock_client)
    yield mock_client


def test_init(processor_with_mocks):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    assert processor.dataset
    assert processor.share
    assert processor.shared_db_name == 'gluedatabase_shared'


def test_get_share_principals(
    mocker,
    processor_with_mocks,
    source_environment: Environment,
    target_environment: Environment,
    share: ShareObject,
):
    # Given a dataset and its share, build db_share name
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    get_iam_role_arn_mock = mocker.patch(
        'dataall.base.aws.iam.IAM.get_role_arn_by_name',
        side_effect=lambda account_id, region, role_name: f'arn:aws:iam::{account_id}:role/{role_name}',
    )

    # Then, it should return
    assert processor.get_share_principals() == [
        f'arn:aws:iam::{target_environment.AwsAccountId}:role/{share.principalIAMRoleName}'
    ]
    get_iam_role_arn_mock.assert_called_once()


def test_build_shared_db_name(processor_with_mocks, dataset1: Dataset, mock_glue_client):
    # Given a new share, build db_share name
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mock_glue_client().get_glue_database.return_value = False
    # Reset to remove call in __init__
    mock_glue_client().get_glue_database.reset_mock()
    # Then
    assert processor.build_shared_db_name() == (f'{dataset1.GlueDatabaseName[:247]}_shared', True)
    mock_glue_client().get_glue_database.assert_called_once()


def test_build_shared_db_name_old(processor_with_mocks, dataset1: Dataset, share: ShareObject, mock_glue_client):
    # Given an existing old share (shared db name with shareUri), build db_share name
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mock_glue_client().get_glue_database.return_value = True
    # Reset to remove call in __init__
    mock_glue_client().get_glue_database.reset_mock()
    # Then
    assert processor.build_shared_db_name() == (f'{dataset1.GlueDatabaseName}_shared_{share.shareUri}'[:254], False)
    mock_glue_client().get_glue_database.assert_called_once()


def test_check_table_exists_in_source_database(
    processor_with_mocks, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = True
    # When
    processor.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_check_table_exists_in_source_database_exception(
    processor_with_mocks, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = False
    # When
    with pytest.raises(Exception) as exception:
        processor.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)
    assert 'ExceptionInfo' in str(exception)


def test_check_resource_link_table_exists_in_target_database_true(processor_with_mocks, table1: DatasetTable):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = True
    # When
    response = processor.check_resource_link_table_exists_in_target_database(table=table1)
    # Then
    assert response == True
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_check_resource_link_table_exists_in_target_database_false(
    processor_with_mocks,
    table1: DatasetTable,
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = False
    # Then
    assert processor.check_resource_link_table_exists_in_target_database(table=table1) == False
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_revoke_iam_allowed_principals_from_table(processor_with_mocks, table1: DatasetTable, source_environment):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.revoke_permissions_from_table.return_value = True
    # Then
    assert processor.revoke_iam_allowed_principals_from_table(table1) == True
    lf_client.revoke_permissions_from_table.assert_called_once()
    lf_client.revoke_permissions_from_table.assert_called_with(
        principals=['EVERYONE'],
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['ALL'],
    )


def test_grant_pivot_role_all_database_permissions_to_source_database(
    processor_with_mocks, dataset1: Dataset, source_environment: Environment, mocker
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.grant_permissions_to_database.return_value = True
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # Then
    assert processor.grant_pivot_role_all_database_permissions_to_source_database() == True
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=dataset1.GlueDatabaseName,
        permissions=['ALL'],
    )


def test_check_if_exists_and_create_shared_database_in_target(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.create_database.return_value = True
    # When
    processor.check_if_exists_and_create_shared_database_in_target()
    # Then
    glue_client.create_database.assert_called_once()
    glue_client.create_database.assert_called_with(location=f's3://{dataset1.S3BucketName}')


def test_grant_pivot_role_all_database_permissions_to_shared_database(processor_with_mocks, dataset1: Dataset, mocker):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    processor.grant_pivot_role_all_database_permissions_to_shared_database()
    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['ALL'],
    )


def test_grant_principals_database_permissions_to_shared_database(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.grant_principals_database_permissions_to_shared_database()
    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    lf_client.grant_permissions_to_database.assert_called_with(
        principals=processor.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_grant_target_account_permissions_to_source_table(
    processor_with_mocks, target_environment: Environment, source_environment: Environment, table1: DatasetTable
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.grant_target_account_permissions_to_source_table(table1)
    # Then
    lf_client.grant_permissions_to_table.assert_called_once()
    lf_client.grant_permissions_to_table.assert_called_with(
        principals=[target_environment.AwsAccountId],
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
        permissions_with_grant_options=['DESCRIBE', 'SELECT'],
    )


def test_check_if_exists_and_create_resource_link_table_in_shared_database_false(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = False
    glue_client.create_resource_link.return_value = True

    # When
    processor.check_if_exists_and_create_resource_link_table_in_shared_database(table1)

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
    processor_with_mocks, table1: DatasetTable
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = True
    glue_client.create_resource_link.return_value = True

    # When
    processor.check_if_exists_and_create_resource_link_table_in_shared_database(table1)

    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.create_resource_link.assert_not_called()


def test_grant_principals_permissions_to_resource_link_table(
    processor_with_mocks, table1: DatasetTable, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.grant_principals_permissions_to_resource_link_table(table1)
    # Then
    lf_client.grant_permissions_to_table.assert_called_once()
    lf_client.grant_permissions_to_table.assert_called_with(
        principals=processor.principals,
        database_name=processor.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_grant_pivot_role_drop_permissions_to_resource_link_table(
    processor_with_mocks, table1: DatasetTable, target_environment: Environment, mocker
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    processor.grant_pivot_role_drop_permissions_to_resource_link_table(table1)
    # Then
    lf_client.grant_permissions_to_table.assert_called_once()
    lf_client.grant_permissions_to_table.assert_called_with(
        principals=['arn:role'],
        database_name=processor.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DROP'],
    )


def test_grant_principals_permissions_to_table_in_target(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.grant_principals_permissions_to_table_in_target(table1)
    # Then
    lf_client.grant_permissions_to_table_with_columns.assert_called_once()
    lf_client.grant_permissions_to_table_with_columns.assert_called_with(
        principals=processor.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_check_pivot_role_permissions_to_source_database(processor_with_mocks, dataset1: Dataset, mocker):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_database.return_value = True
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # When
    processor.check_pivot_role_permissions_to_source_database()
    # Then
    assert len(processor.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=dataset1.GlueDatabaseName,
        permissions=['ALL'],
    )


def test_check_pivot_role_permissions_to_source_database_failed(processor_with_mocks, dataset1: Dataset, mocker):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_database.return_value = False
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    # Then
    processor.check_pivot_role_permissions_to_source_database()
    assert len(processor.db_level_errors) == 1


def test_check_shared_database_in_target(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.get_glue_database.return_value = True
    # When
    processor.check_shared_database_in_target()
    # Then
    glue_client.get_glue_database.assert_called_once()
    assert len(processor.db_level_errors) == 0


def test_check_shared_database_in_target_failed(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.get_glue_database.return_value = False
    # When
    processor.check_shared_database_in_target()
    # Then
    assert len(processor.db_level_errors) == 1


def test_check_pivot_role_permissions_to_shared_database(processor_with_mocks, dataset1: Dataset, mocker):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    lf_client.check_permissions_to_database.return_value = True
    # When
    processor.check_pivot_role_permissions_to_shared_database()
    # Then
    assert len(processor.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=['arn:role'],
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['ALL'],
    )


def test_check_pivot_role_permissions_to_shared_database_failed(processor_with_mocks, dataset1: Dataset, mocker):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_arn',
        return_value='arn:role',
    )
    lf_client.check_permissions_to_database.return_value = False
    # When
    processor.check_pivot_role_permissions_to_shared_database()
    # Then
    assert len(processor.db_level_errors) == 1


def test_check_principals_permissions_to_shared_database(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_database.return_value = True
    # When
    processor.check_principals_permissions_to_shared_database()
    # Then
    assert len(processor.db_level_errors) == 0
    lf_client.check_permissions_to_database.assert_called_once()
    lf_client.check_permissions_to_database.assert_called_with(
        principals=processor.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_check_principals_permissions_to_shared_database_failed(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_database.return_value = False
    # When
    processor.check_principals_permissions_to_shared_database()
    # Then
    assert len(processor.db_level_errors) == 1


def test_verify_table_exists_in_source_database(
    processor_with_mocks, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = True
    # When
    processor.check_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    assert len(processor.tbl_level_errors) == 0
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_verify_table_exists_in_source_database_failed(
    processor_with_mocks, table1: DatasetTable, share_item: ShareObjectItem, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = False
    # When
    processor.verify_table_exists_in_source_database(share_item=share_item, table=table1)
    # Then
    assert len(processor.tbl_level_errors) == 1


def test_check_target_account_permissions_to_source_table(
    processor_with_mocks, target_environment: Environment, source_environment: Environment, table1: DatasetTable
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table.return_value = True
    # When
    processor.check_target_account_permissions_to_source_table(table1)
    # Then
    assert len(processor.tbl_level_errors) == 0
    lf_client.check_permissions_to_table.assert_called_once()
    lf_client.check_permissions_to_table.assert_called_with(
        principals=[target_environment.AwsAccountId],
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
        permissions_with_grant_options=['DESCRIBE', 'SELECT'],
    )


def test_check_target_account_permissions_to_source_table_failed(
    processor_with_mocks, target_environment: Environment, source_environment: Environment, table1: DatasetTable
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table.return_value = False
    # When
    processor.check_target_account_permissions_to_source_table(table1)
    # Then
    assert len(processor.tbl_level_errors) == 1


def test_verify_resource_link_table_exists_in_target_database(
    processor_with_mocks, table1: DatasetTable, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = True
    # When
    processor.verify_resource_link_table_exists_in_target_database(table=table1)
    # Then
    assert len(processor.tbl_level_errors) == 0
    glue_client.table_exists.assert_called_once()
    glue_client.table_exists.assert_called_with(table1.GlueTableName)


def test_verify_resource_link_table_exists_in_target_database_failed(
    processor_with_mocks, table1: DatasetTable, mock_glue_client
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    glue_client.table_exists.return_value = False
    # When
    processor.verify_resource_link_table_exists_in_target_database(table=table1)
    # Then
    assert len(processor.tbl_level_errors) == 1


def test_check_principals_permissions_to_resource_link_table(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table_with_columns.return_value = True
    # When
    processor.check_principals_permissions_to_resource_link_table(table1)
    # Then
    assert len(processor.tbl_level_errors) == 0
    lf_client.check_permissions_to_table_with_columns.assert_called_once()
    lf_client.check_permissions_to_table_with_columns.assert_called_with(
        principals=processor.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_check_principals_permissions_to_resource_link_table_failed(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table_with_columns.return_value = False
    # When
    processor.check_principals_permissions_to_resource_link_table(table1)
    # Then
    assert len(processor.tbl_level_errors) == 1


def test_check_principals_permissions_to_table_in_target(
    processor_with_mocks, table1: DatasetTable, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table.return_value = True
    # When
    processor.check_principals_permissions_to_table_in_target(table1)
    # Then
    assert len(processor.tbl_level_errors) == 0
    lf_client.check_permissions_to_table.assert_called_once()
    lf_client.check_permissions_to_table.assert_called_with(
        principals=processor.principals,
        database_name=processor.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_check_principals_permissions_to_table_in_target_failed(
    processor_with_mocks, table1: DatasetTable, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    lf_client.check_permissions_to_table.return_value = False
    # When
    processor.check_principals_permissions_to_table_in_target(table1)
    # Then
    assert len(processor.tbl_level_errors) == 1


def test_revoke_principals_permissions_to_resource_link_table(
    processor_with_mocks, table1: DatasetTable, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.revoke_principals_permissions_to_resource_link_table(table=table1)
    # Then
    lf_client.revoke_permissions_from_table.assert_called_once()
    lf_client.revoke_permissions_from_table.assert_called_with(
        principals=processor.principals,
        database_name=processor.shared_db_name,
        table_name=table1.GlueTableName,
        catalog_id=target_environment.AwsAccountId,
        permissions=['DESCRIBE'],
    )


def test_revoke_principals_permissions_to_table_in_target(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.revoke_principals_permissions_to_table_in_target(table=table1, other_table_shares_in_env=False)
    # Then
    lf_client.revoke_permissions_from_table_with_columns.assert_called_once()
    lf_client.revoke_permissions_from_table_with_columns.assert_called_with(
        principals=processor.principals,
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
    )


def test_delete_resource_link_table_in_shared_database_true(processor_with_mocks, table2: DatasetTable):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

    # When
    processor.delete_resource_link_table_in_shared_database(table=table2)
    # Then
    glue_client.table_exists.assert_called_once()
    glue_client.delete_table.assert_called_once()


def test_revoke_principals_database_permissions_to_shared_database(processor_with_mocks, dataset1: Dataset):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.revoke_principals_database_permissions_to_shared_database()
    # Then
    lf_client.revoke_permissions_to_database.assert_called_once()
    lf_client.revoke_permissions_to_database.assert_called_with(
        principals=processor.principals,
        database_name=f'{dataset1.GlueDatabaseName}_shared',
        permissions=['DESCRIBE'],
    )


def test_delete_shared_database_in_target(
    processor_with_mocks,
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.delete_shared_database_in_target()
    # Then
    glue_client.delete_database.assert_called_once()


def test_revoke_external_account_access_on_source_account(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks
    # When
    processor.revoke_external_account_access_on_source_account(table1)
    # Then
    lf_client.revoke_permissions_from_table_with_columns.assert_called_once()
    lf_client.revoke_permissions_from_table_with_columns.assert_called_with(
        principals=[target_environment.AwsAccountId],
        database_name=table1.GlueDatabaseName,
        table_name=table1.GlueTableName,
        catalog_id=source_environment.AwsAccountId,
        permissions=['DESCRIBE', 'SELECT'],
        permissions_with_grant_options=['DESCRIBE', 'SELECT'],
    )


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists(
    db,
    dataset1,
    share,
    table1,
    table2,
    source_environment,
    target_environment,
    target_environment_group,
    mock_glue_client,
    mocker,
):
    # Mock glue and sts calls to create a LF processor
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.remote_session',
        return_value=boto3.Session(),
    )
    mocker.patch(
        'dataall.base.aws.iam.IAM.get_role_arn_by_name',
        side_effect=lambda account_id, role_name: f'arn:aws:iam::{account_id}:role/{role_name}',
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
        processor = ProcessLakeFormationShare(
            session,
            dataset1,
            share,
            [table1],
            source_environment,
            target_environment,
            target_environment_group,
        )

        # Check if the catalog account exists
        assert processor.check_catalog_account_exists_and_verify() == True
        # Then
        # Check the source account id. source account database and region to check if it is updated
        assert processor.source_account_id == '12129101212'
        assert processor.source_database_name == 'catalog_db'
        assert processor.source_account_region == 'us-east-1'

        # Check the shared database
        assert processor.shared_db_name == 'catalog_db' + '_shared'


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists_and_pivot_role_not_assumable(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment, target_environment: Environment, mocker
):
    # Given
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

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
        processor._verify_catalog_ownership('12129101212', 'us-east-1', 'catalog_db')

    # Then
    assert 'Pivot role is not assumable' in str(exception)
    assert processor.check_catalog_account_exists_and_verify() is None


def test_check_catalog_account_exists_and_update_processor_with_catalog_exists_and_tag_doesnt_exists(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment, target_environment: Environment, mocker
):
    # Given
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

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
        processor._validate_catalog_ownership_tag('12129101212', 'us-east-1', 'catalog_db')

    # then
    assert processor.check_catalog_account_exists_and_verify() is None
    assert 'owner_account_id tag does not exist or does not matches the source account id' in str(exception)


def test_check_catalog_account_exists_and_update_processor_with_catalog_doesnt_exists(
    processor_with_mocks, table1: DatasetTable, source_environment: Environment, target_environment: Environment
):
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

    # When
    assert processor.check_catalog_account_exists_and_verify() == False

    # Then
    # Check the source account id. source account database and region to check if it is updated
    assert processor.source_account_id == source_environment.AwsAccountId
    assert processor.source_database_name == processor.dataset.GlueDatabaseName
    assert processor.source_account_region == source_environment.region

    # Check the shared database
    assert processor.shared_db_name == processor.dataset.GlueDatabaseName + '_shared'


def test_handle_share_failure(processor_with_mocks, table1: DatasetTable, mocker):
    # Given
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, 'trigger_table_sharing_failure_alarm')
    error = Exception()
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

    # When
    processor.handle_share_failure(table1, error)

    # Then
    alarm_service_mock.assert_called_once()


def test_handle_revoke_failure(
    processor_with_mocks,
    table1: DatasetTable,
    mocker,
):
    # Given
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, 'trigger_revoke_table_sharing_failure_alarm')
    error = Exception()
    processor, lf_client, glue_client, mock_glue_client = processor_with_mocks

    # When
    processor.handle_revoke_failure(table1, error)

    # Then
    alarm_service_mock.assert_called_once()
