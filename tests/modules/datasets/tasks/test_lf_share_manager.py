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
from dataall.modules.dataset_sharing.api.enums import ShareItemStatus
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject, ShareObjectItem
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.dataset_sharing.services.dataset_alarm_service import DatasetAlarmService
from dataall.modules.dataset_sharing.services.share_processors.lakeformation_process_share import ProcessLakeFormationShare
from dataall.modules.dataset_sharing.aws.lakeformation_client import LakeFormationClient
from dataall.modules.dataset_sharing.aws.glue_client import GlueClient

SOURCE_ENV_ACCOUNT = "1" *  12
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"


TARGET_ACCOUNT_ENV = "2" * 12
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"


@pytest.fixture(scope="module")
def source_environment(env: Callable, org_fixture: Organization, group: Group) -> Environment:
    yield env(
        org=org_fixture,
        account=SOURCE_ENV_ACCOUNT,
        envname="source_environment",
        owner=group.owner,
        group=group.name,
        role=SOURCE_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module")
def target_environment(env: Callable, org_fixture: Organization, group2: Group) -> Environment:
    yield env(
        org=org_fixture,
        account=TARGET_ACCOUNT_ENV,
        envname="target_environment",
        owner=group2.owner,
        group=group2.name,
        role=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module")
def target_environment_group(environment_group: Callable, target_environment: Environment,
                             group2: Group) -> EnvironmentGroup:
    yield environment_group(
        environment=target_environment,
        group=group2.name
    )


@pytest.fixture(scope="module")
def dataset1(create_dataset: Callable, org_fixture: Organization, source_environment: Environment) -> Dataset:
    yield create_dataset(
        organization=org_fixture,
        environment=source_environment,
        label="dataset1"
    )


@pytest.fixture(scope="module")
def table1(table: Callable, dataset1: Dataset) -> DatasetTable:
    yield table(
        dataset=dataset1,
        label="table1"
    )


@pytest.fixture(scope="module")
def table2(table: Callable, dataset1: Dataset) -> DatasetTable:
    yield table(
        dataset=dataset1,
        label="table2"
    )


@pytest.fixture(scope="module")
def share(
        share: Callable, dataset1: Dataset, target_environment: Environment,
        target_environment_group: EnvironmentGroup) -> ShareObject:
    yield share(
        dataset=dataset1,
        environment=target_environment,
        env_group=target_environment_group
    )

@pytest.fixture(scope="module")
def share_item(share_item_table: Callable, share: ShareObject,
                             table1: DatasetTable) -> ShareObjectItem:
    yield share_item_table(
        share=share,
        table=table1,
        status=ShareItemStatus.Share_Approved.value
    )


@pytest.fixture(scope="function", autouse=True)
def processor_with_mocks(db, dataset1, share, table1, table2, source_environment, target_environment,
                            target_environment_group, mocker):
    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.remote_session",
        return_value=boto3.Session(),
    )
    mocker.patch(
        "dataall.base.aws.iam.IAM.get_role_arn_by_name",
        side_effect=lambda account_id, role_name: f"arn:aws:iam::{account_id}:role/{role_name}"
    )
    with db.scoped_session() as session:
        processor = ProcessLakeFormationShare(
            session,
            dataset1,
            share,
            [table1],
            [table2],
            source_environment,
            target_environment,
            target_environment_group,
        )
        lf_mock_client = MagicMock()
        lf_mock_client().grant_permissions_to_database.return_value = True
        lf_mock_client().grant_permissions_to_table.return_value = True
        lf_mock_client().grant_permissions_to_table_with_columns.return_value = True
        lf_mock_client().batch_revoke_permissions_from_table.return_value = True
        lf_mock_client().batch_revoke_permissions_from_table_with_columns.return_value = True
        lf_mock_client().revoke_permissions_from_table.return_value = True
        lf_mock_client().revoke_permissions_from_table_with_columns.return_value = True

        mocker.patch.object(
            processor,
            "lf_client_in_target",
            lf_mock_client,
        )
        mocker.patch.object(
            processor,
            "lf_client_in_source",
            lf_mock_client
        )
        glue_mock_client = MagicMock()
        glue_mock_client().create_database.return_value = True
        glue_mock_client().get_glue_database.return_value = True
        glue_mock_client().table_exists.return_value = True
        glue_mock_client().delete_table.return_value = True
        glue_mock_client().create_resource_link.return_value = True
        glue_mock_client().delete_database.return_value = True

        mocker.patch.object(
            processor,
            "glue_client_in_target",
            glue_mock_client
        )

    yield processor, lf_mock_client, glue_mock_client



@pytest.fixture(scope="function")
def mock_glue_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "dataall.modules.dataset_sharing.services.share_managers.lf_share_manager.GlueClient",
        mock_client
    )
    yield mock_client


def test_init(processor_with_mocks):
    processor, lf_client, glue_client = processor_with_mocks
    assert processor.dataset
    assert processor.share

def test_get_share_principals(
        mocker,
        processor_with_mocks,
        source_environment: Environment,
        target_environment: Environment,
        share: ShareObject,
):
    # Given a dataset and its share, build db_share name
    processor, lf_client, glue_client = processor_with_mocks
    get_iam_role_arn_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.get_role_arn_by_name",
        side_effect = lambda account_id, role_name : f"arn:aws:iam::{account_id}:role/{role_name}"
    )

    # Then, it should return
    assert processor.get_share_principals() == [f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share.principalIAMRoleName}"]
    get_iam_role_arn_mock.assert_called_once()


def test_build_shared_db_name(
        processor_with_mocks,
        dataset1: Dataset
):
    # Given a dataset and its share, build db_share name
    processor, lf_client, glue_client = processor_with_mocks
    # Then, it should return
    assert processor.build_shared_db_name() == (f"{dataset1.GlueDatabaseName[:247]}_shared", True)

def test_check_table_exists_in_source_database(
        processor_with_mocks,
        table1: DatasetTable,
        share_item: ShareObjectItem,
        mock_glue_client
):
    processor, lf_client, glue_client = processor_with_mocks
    mock_glue_client().table_exists.return_value = True

    # When
    processor.check_table_exists_in_source_database(
        share_item=share_item,
        table=table1
    )
    # Then
    mock_glue_client().table_exists.assert_called_once()


def test_check_resource_link_table_exists_in_target_database(
        processor_with_mocks,
        table1: DatasetTable,
        mock_glue_client
):
    processor, lf_client, glue_client = processor_with_mocks
    mock_glue_client().table_exists.return_value = True

    # When
    processor.check_resource_link_table_exists_in_target_database(table=table1)
    # Then
    mock_glue_client().table_exists.assert_called_once()

def test_revoke_iam_allowed_principals_from_table(
        processor_with_mocks,
        table1: DatasetTable
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.revoke_iam_allowed_principals_from_table(table1)
    # Then
    lf_client.revoke_permissions_from_table.assert_called_once()


def test_grant_pivot_role_all_database_permissions_to_source_database(
        processor_with_mocks
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.grant_pivot_role_all_database_permissions_to_source_database()

    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    #TODO: ADD ARGUMENTS


def test_check_if_exists_and_create_shared_database_in_target(
        processor_with_mocks
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.check_if_exists_and_create_shared_database_in_target()

    # Then
    glue_client.create_database.assert_called_once()


def test_grant_pivot_role_all_database_permissions_to_shared_database(
        processor_with_mocks
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.grant_pivot_role_all_database_permissions_to_shared_database()

    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    #TODO: ADD ARGUMENTS


def test_grant_principals_permissions_to_shared_database(
        processor_with_mocks
):
    processor, lf_client, glue_client = processor_with_mocks
    # When
    processor.grant_principals_database_permissions_to_shared_database()

    # Then
    lf_client.grant_permissions_to_database.assert_called_once()
    #TODO: ADD ARGUMENTS
    # TODO: called X numbner of principals times


def test_grant_target_account_permissions_to_source_table():
    # TODO
    pass

def test_check_if_exists_and_create_resource_link_table_in_shared_database(
        processor_with_mocks,
        table1: DatasetTable,
        mock_glue_client
):
    processor, lf_client, glue_client = processor_with_mocks
    mock_glue_client().table_exists.return_value = False

    # When
    processor.check_if_exists_and_create_resource_link_table_in_shared_database(table1)

    # Then
    mock_glue_client().table_exists.assert_called_once()
    glue_client.create_resource_link.assert_called_once()
    #TODO add call arguments


def test_grant_principals_permissions_to_resource_link_table():
    #TODO
    pass

def test_grant_principals_permissions_to_table_in_target():
    #TODO
    pass

def test_revoke_principals_permissions_to_resource_link_table(
    processor_with_mocks,
    table1: DatasetTable
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.revoke_principals_permissions_to_resource_link_table(table=table1)

    # Then
    lf_client.batch_revoke_permissions_from_table.assert_called_once()



def test_revoke_principals_permissions_to_table_in_target(
    processor_with_mocks,
    table1: DatasetTable,
):
    processor, lf_client, glue_client = processor_with_mocks

    processor.revoke_principals_permissions_to_table_in_target(table = table1)

    # Then
    lf_client.revoke_permissions_from_table_with_columns.assert_called_once()



def test_delete_resource_link_table_in_shared_database(
    processor_with_mocks,
    table2: DatasetTable
):
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.delete_resource_link_table_in_shared_database(
        table=table2
    )
    # Then
    glue_client.delete_table.assert_called_once()


def test_delete_shared_database_in_target(
    processor_with_mocks,
):
    processor, lf_client, glue_client = processor_with_mocks
    # When
    processor.delete_shared_database_in_target()
    # Then
    glue_client.delete_database.assert_called_once()


def test_revoke_external_account_access_on_source_account(
    processor_with_mocks,
    table1: DatasetTable
):
    processor, lf_client, glue_client = processor_with_mocks
    # When
    processor.revoke_external_account_access_on_source_account(table1)
    # Then
    lf_client.revoke_permissions_from_table_with_columns.assert_called_once()


def test_handle_share_failure(
        processor_with_mocks,
        table1: DatasetTable,
        mocker
):
    # Given
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, "trigger_table_sharing_failure_alarm")
    error = Exception
    processor, lf_client, glue_client = processor_with_mocks

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
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, "trigger_revoke_table_sharing_failure_alarm")
    error = Exception
    processor, lf_client, glue_client = processor_with_mocks

    # When
    processor.handle_revoke_failure(table1, error)

    # Then
    alarm_service_mock.assert_called_once()

