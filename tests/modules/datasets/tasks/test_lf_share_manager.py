"""
Testing LF manager class methods invoked in same account and cross account LF share processors.
Remarks

"""
from unittest.mock import MagicMock

import boto3
import pytest

from typing import Callable

from dataall.core.cognito_groups.db.cognito_group_models import Group
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.api.enums import ShareItemStatus
from dataall.modules.dataset_sharing.db.models import ShareObject, ShareObjectItem
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.modules.dataset_sharing.services.dataset_alarm_service import DatasetAlarmService

from dataall.modules.dataset_sharing.services.share_processors.lf_process_cross_account_share import ProcessLFCrossAccountShare
from dataall.modules.dataset_sharing.services.share_processors.lf_process_same_account_share import ProcessLFSameAccountShare


SOURCE_ENV_ACCOUNT = "1" *  12
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"


TARGET_ACCOUNT_ENV = "2" * 12
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"

LF_CLIENT = "dataall.modules.dataset_sharing.aws.lakeformation_client.LakeFormationClient"


@pytest.fixture(scope="module")
def org1(org: Callable) -> Organization:
    yield org(
        label="org",
        owner="alice",
        SamlGroupName="admins"
    )


@pytest.fixture(scope="module")
def source_environment(environment: Callable, org1: Organization, group: Group) -> Environment:
    yield environment(
        organization=org1,
        awsAccountId=SOURCE_ENV_ACCOUNT,
        label="source_environment",
        owner=group.owner,
        samlGroupName=group.name,
        environmentDefaultIAMRoleName=SOURCE_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module")
def source_environment_group(environment_group: Callable, source_environment: Environment,
                             group: Group) -> EnvironmentGroup:
    yield environment_group(
        environment=source_environment,
        group=group
    )


@pytest.fixture(scope="module")
def source_environment_group_requesters(environment_group: Callable, source_environment: Environment,
                                        group2: Group) -> EnvironmentGroup:
    yield environment_group(
        environment=source_environment,
        group=group2
    )


@pytest.fixture(scope="module")
def target_environment(environment: Callable, org1: Organization, group2: Group) -> Environment:
    yield environment(
        organization=org1,
        awsAccountId=TARGET_ACCOUNT_ENV,
        label="target_environment",
        owner=group2.owner,
        samlGroupName=group2.name,
        environmentDefaultIAMRoleName=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module")
def target_environment_group(environment_group: Callable, target_environment: Environment,
                             group2: Group) -> EnvironmentGroup:
    yield environment_group(
        environment=target_environment,
        group=group2
    )


@pytest.fixture(scope="module")
def dataset1(dataset: Callable, org1: Organization, source_environment: Environment) -> Dataset:
    yield dataset(
        organization=org1,
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
def share_same_account(
        share: Callable, dataset1: Dataset, source_environment: Environment,
        source_environment_group_requesters: EnvironmentGroup) -> ShareObject:
    yield share(
        dataset=dataset1,
        environment=source_environment,
        env_group=source_environment_group_requesters
    )


@pytest.fixture(scope="module")
def share_cross_account(
        share: Callable, dataset1: Dataset, target_environment: Environment,
        target_environment_group: EnvironmentGroup) -> ShareObject:
    yield share(
        dataset=dataset1,
        environment=target_environment,
        env_group=target_environment_group
    )


@pytest.fixture(scope="module")
def share_item_same_account(share_item_table: Callable, share_same_account: ShareObject,
                            table1: DatasetTable) -> ShareObjectItem:
    yield share_item_table(
        share=share_same_account,
        table=table1,
        status=ShareItemStatus.Share_Approved.value
    )

@pytest.fixture(scope="module")
def revoke_item_same_account(share_item_table: Callable, share_same_account: ShareObject,
                             table2: DatasetTable) -> ShareObjectItem:
    yield share_item_table(
        share=share_same_account,
        table=table2,
        status=ShareItemStatus.Revoke_Approved.value
    )

@pytest.fixture(scope="module")
def share_item_cross_account(share_item_table: Callable, share_cross_account: ShareObject,
                             table1: DatasetTable) -> ShareObjectItem:
    yield share_item_table(
        share=share_cross_account,
        table=table1,
        status=ShareItemStatus.Share_Approved.value
    )


@pytest.fixture(scope="module")
def revoke_item_cross_account(share_item_table: Callable, share_cross_account: ShareObject,
                              table2: DatasetTable) -> ShareObjectItem:
    yield share_item_table(
        share=share_cross_account,
        table=table2,
        status=ShareItemStatus.Revoke_Approved.value
    )


@pytest.fixture(scope="module", autouse=True)
def processor_cross_account(db, dataset1, share_cross_account, table1, table2, source_environment, target_environment,
                            target_environment_group):
    with db.scoped_session() as session:
        processor = ProcessLFCrossAccountShare(
            session,
            dataset1,
            share_cross_account,
            [table1],
            [table2],
            source_environment,
            target_environment,
            target_environment_group,
        )
    yield processor


@pytest.fixture(scope="module", autouse=True)
def processor_same_account(db, dataset1, share_same_account, table1, source_environment,
                           source_environment_group_requesters):
    with db.scoped_session() as session:
        processor = ProcessLFSameAccountShare(
            session,
            dataset1,
            share_same_account,
            [table1],
            [table2],
            source_environment,
            source_environment,
            source_environment_group_requesters,
        )
    yield processor


@pytest.fixture(scope="function")
def mock_glue_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "dataall.modules.dataset_sharing.services.share_managers.lf_share_manager.GlueClient",
        mock_client
    )
    yield mock_client


def test_init(processor_same_account, processor_cross_account):
    assert processor_same_account.dataset
    assert processor_same_account.share


def test_build_shared_db_name(
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        dataset1: Dataset,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
):
    # Given a dataset and its share, build db_share name
    # Then, it should return
    assert processor_same_account.build_shared_db_name() == (dataset1.GlueDatabaseName + '_shared_' + share_same_account.shareUri)[:254]
    assert processor_cross_account.build_shared_db_name() == (dataset1.GlueDatabaseName + '_shared_' + share_cross_account.shareUri)[:254]


def test_get_share_principals(
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        source_environment: Environment,
        target_environment: Environment,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
):
    # Given a dataset and its share, build db_share name
    # Then, it should return
    assert processor_same_account.get_share_principals() == [f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"]
    assert processor_cross_account.get_share_principals() == [f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"]


def test_create_shared_database(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        mocker,
        mock_glue_client
):
    mock_glue_client().create_database.return_value = True

    lf_mock_pr = mocker.patch(
        f"{LF_CLIENT}.grant_pivot_role_all_database_permissions",
        return_value=True,
    )
    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.remote_session",
        return_value=boto3.Session(),
    )
    lf_mock = mocker.patch(
        f"{LF_CLIENT}.grant_permissions_to_database",
        return_value=True,
    )
    # When
    processor_same_account.create_shared_database(
        target_environment=source_environment,
        dataset=dataset1,
        shared_db_name=(dataset1.GlueDatabaseName + '_shared_' + share_same_account.shareUri)[:254],
        principals=[f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"]
    )

    # Then
    mock_glue_client().create_database.assert_called_once()
    lf_mock_pr.assert_called_once()
    lf_mock.assert_called_once()

    # Reset mocks
    mock_glue_client().create_database.reset_mock()
    lf_mock_pr.reset_mock()
    lf_mock.reset_mock()

    # When
    processor_cross_account.create_shared_database(
        target_environment=target_environment,
        dataset=dataset1,
        shared_db_name=(dataset1.GlueDatabaseName + '_shared_' + share_cross_account.shareUri)[:254],
        principals=[f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"]
    )

    # Then
    mock_glue_client().create_database.assert_called_once()
    lf_mock_pr.assert_called_once()
    lf_mock.assert_called_once()


def test_check_share_item_exists_on_glue_catalog(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        table1: DatasetTable,
        share_item_same_account: ShareObjectItem,
        share_item_cross_account: ShareObjectItem,
        mocker,
        mock_glue_client,
):

    mock_glue_client().table_exists.return_value = True

    # When
    processor_same_account.check_share_item_exists_on_glue_catalog(
        share_item=share_item_same_account,
        table=table1
    )
    # Then
    mock_glue_client().table_exists.assert_called_once()
    mock_glue_client().table_exists.reset_mock()

    # When
    processor_cross_account.check_share_item_exists_on_glue_catalog(
        share_item=share_item_cross_account,
        table=table1
    )
    # Then
    mock_glue_client().table_exists.assert_called_once()


def test_build_share_data(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table1: DatasetTable,
):
    data_same_account = {
        'source': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'database': table1.GlueDatabaseName,
            'tablename': table1.GlueTableName,
        },
        'target': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'principals': [f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"],
            'database': (dataset1.GlueDatabaseName + '_shared_' + share_same_account.shareUri)[:254],
        },
    }

    data = processor_same_account.build_share_data(table=table1)
    assert data == data_same_account

    data_cross_account = {
        'source': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'database': table1.GlueDatabaseName,
            'tablename': table1.GlueTableName,
        },
        'target': {
            'accountid': target_environment.AwsAccountId,
            'region': target_environment.region,
            'principals': [f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"],
            'database': (dataset1.GlueDatabaseName + '_shared_' + share_cross_account.shareUri)[:254],
        },
    }

    data = processor_cross_account.build_share_data(table=table1)
    assert data == data_cross_account


def test_create_resource_link(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table1: DatasetTable,
        mocker,
        mock_glue_client,
):
    sts_mock = mocker.patch(
        "dataall.base.aws.sts.SessionHelper.remote_session",
        return_value=boto3.Session(),
    )
    glue_mock = mock_glue_client().create_resource_link
    glue_mock.return_value = True

    lf_mock_1 = mocker.patch(
        f"{LF_CLIENT}.grant_resource_link_permission",
        return_value=True,
    )
    lf_mock_2 = mocker.patch(
        f"{LF_CLIENT}.grant_resource_link_permission_on_target",
        return_value=True,
    )

    # When
    data_same_account = {
        'source': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'database': table1.GlueDatabaseName,
            'tablename': table1.GlueTableName,
        },
        'target': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'principals': [f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"],
            'database': (dataset1.GlueDatabaseName + '_shared_' + share_same_account.shareUri)[:254],
        },
    }
    processor_same_account.create_resource_link(**data_same_account)

    # Then
    sts_mock.assert_called_once()
    glue_mock.assert_called_once()
    lf_mock_1.assert_called_once()
    lf_mock_2.assert_called_once()

    # Reset mocks
    sts_mock.reset_mock()
    glue_mock.reset_mock()
    lf_mock_1.reset_mock()
    lf_mock_2.reset_mock()


    data_cross_account = {
        'source': {
            'accountid': source_environment.AwsAccountId,
            'region': source_environment.region,
            'database': table1.GlueDatabaseName,
            'tablename': table1.GlueTableName,
        },
        'target': {
            'accountid': target_environment.AwsAccountId,
            'region': target_environment.region,
            'principals': [f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"],
            'database': (dataset1.GlueDatabaseName + '_shared_' + share_cross_account.shareUri)[:254],
        },
    }
    processor_cross_account.create_resource_link(**data_cross_account)

    # Then
    sts_mock.assert_called_once()
    glue_mock.assert_called_once()
    lf_mock_1.assert_called_once()
    lf_mock_2.assert_called_once()

    pass


def test_revoke_table_resource_link_access(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table2: DatasetTable,
        mocker,
        mock_glue_client
):

    glue_mock = mock_glue_client().table_exists
    glue_mock.return_value = True

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.remote_session",
        return_value=boto3.Session(),
    )

    lf_mock = mocker.patch(
        f"{LF_CLIENT}.batch_revoke_permissions",
        return_value=True,
    )

    processor_same_account.revoke_table_resource_link_access(
        table=table2,
        principals=[f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"]
    )
    # Then
    glue_mock.assert_called_once()
    lf_mock.assert_called_once()

    # Reset mocks
    glue_mock.reset_mock()
    lf_mock.reset_mock()

    processor_cross_account.revoke_table_resource_link_access(
        table=table2,
        principals=[f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"],
    )
    # Then
    glue_mock.assert_called_once()
    lf_mock.assert_called_once()


def test_revoke_source_table_access(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table2: DatasetTable,
        mocker,
        mock_glue_client
):
    glue_mock = mock_glue_client().table_exists
    glue_mock.return_value = True

    lf_mock = mocker.patch(
        f"{LF_CLIENT}.revoke_source_table_access",
        return_value=True,
    )

    processor_same_account.revoke_source_table_access(
        table=table2,
        principals=[f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"]
    )
    # Then
    glue_mock.assert_called_once()
    lf_mock.assert_called_once()

    # Reset mocks
    glue_mock.reset_mock()
    lf_mock.reset_mock()

    processor_cross_account.revoke_source_table_access(
        table=table2,
        principals=[f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"]
    )
    # Then
    glue_mock.assert_called_once()
    lf_mock.assert_called_once()


def test_delete_resource_link_table(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table2: DatasetTable,
        mock_glue_client
):
    glue_mock = mock_glue_client().table_exists
    glue_mock.return_value = True,

    glue_mock2 = mock_glue_client().delete_table
    glue_mock2.return_value = True,


    processor_same_account.delete_resource_link_table(
        table=table2
    )
    # Then
    glue_mock.assert_called_once()
    glue_mock2.assert_called_once()

    # Reset mocks
    glue_mock.reset_mock()
    glue_mock2.reset_mock()

    processor_cross_account.delete_resource_link_table(
        table=table2
    )
    # Then
    glue_mock.assert_called_once()
    glue_mock2.assert_called_once()


def test_delete_shared_database(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table1: DatasetTable,
        mock_glue_client
):
    glue_mock = mock_glue_client().delete_database
    glue_mock.return_value = True

    processor_same_account.delete_shared_database()
    # Then
    glue_mock.assert_called_once()

    # Reset mocks
    glue_mock.reset_mock()

    processor_cross_account.delete_shared_database()
    # Then
    glue_mock.assert_called_once()


def test_revoke_external_account_access_on_source_account(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_same_account: ShareObject,
        share_cross_account: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        dataset1: Dataset,
        table1: DatasetTable,
        table2: DatasetTable,
        mocker,
):
    lf_mock = mocker.patch(f"{LF_CLIENT}.batch_revoke_permissions", return_value=True)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.remote_session",
        return_value=boto3.Session(),
    )

    processor_cross_account.revoke_external_account_access_on_source_account()
    # Then
    lf_mock.assert_called_once()


def test_handle_share_failure(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        share_item_same_account: ShareObjectItem,
        share_item_cross_account: ShareObjectItem,
        table1: DatasetTable,
        mocker,
):

    # Given
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, "trigger_table_sharing_failure_alarm")
    error = Exception

    # When
    processor_same_account.handle_share_failure(table1, share_item_same_account, error)

    # Then
    alarm_service_mock.assert_called_once()

    # Reset mock
    alarm_service_mock.reset_mock()

    # When
    processor_cross_account.handle_share_failure(table1, share_item_cross_account, error)

    # Then
    alarm_service_mock.assert_called_once()


def test_handle_revoke_failure(
        db,
        processor_same_account: ProcessLFSameAccountShare,
        processor_cross_account: ProcessLFCrossAccountShare,
        revoke_item_same_account: ShareObjectItem,
        revoke_item_cross_account: ShareObjectItem,
        table1: DatasetTable,
        mocker,
):
    # Given
    alarm_service_mock = mocker.patch.object(DatasetAlarmService, "trigger_revoke_table_sharing_failure_alarm")
    error = Exception

    # When
    processor_same_account.handle_revoke_failure(table1, revoke_item_same_account, error)

    # Then
    alarm_service_mock.assert_called_once()

    # Reset mock
    alarm_service_mock.reset_mock()

    # When
    processor_cross_account.handle_revoke_failure(table1, revoke_item_cross_account, error)

    # Then
    alarm_service_mock.assert_called_once()
