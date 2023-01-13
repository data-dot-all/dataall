"""
Testing LF manager class methods invoked in same account and cross account LF share processors.
Remarks

"""
import pytest
import json

from typing import Callable

from dataall.db import models

from dataall.tasks.data_sharing.share_processors.lf_process_cross_account_share import ProcessLFCrossAccountShare
from dataall.tasks.data_sharing.share_processors.lf_process_same_account_share import ProcessLFSameAccountShare
from dataall.utils.alarm_service import AlarmService


SOURCE_ENV_ACCOUNT = "111111111111"
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"


TARGET_ACCOUNT_ENV = "222222222222"
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"


@pytest.fixture(scope="module")
def org1(org: Callable) -> models.Organization:
    yield org(
        label="org",
        owner="alice",
        SamlGroupName="admins"
    )


@pytest.fixture(scope="module", autouse=True)
def source_environment(environment: Callable, org1: models.Organization, group: models.Group) -> models.Environment:
    yield environment(
        organization=org1,
        awsAccountId=SOURCE_ENV_ACCOUNT,
        label="source_environment",
        owner=group.owner,
        samlGroupName=group.name,
        environmentDefaultIAMRoleName=SOURCE_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module", autouse=True)
def source_environment_group(environment_group: Callable, source_environment: models.Environment,
                             group: models.Group) -> models.EnvironmentGroup:
    yield environment_group(
        environment=source_environment,
        group=group
    )


@pytest.fixture(scope="module", autouse=True)
def source_environment_group_requesters(environment_group: Callable, source_environment: models.Environment,
                                        group2: models.Group) -> models.EnvironmentGroup:
    yield environment_group(
        environment=source_environment,
        group=group2
    )


@pytest.fixture(scope="module", autouse=True)
def target_environment(environment: Callable, org1: models.Organization, group2: models.Group) -> models.Environment:
    yield environment(
        organization=org1,
        awsAccountId=TARGET_ACCOUNT_ENV,
        label="target_environment",
        owner=group2.owner,
        samlGroupName=group2.name,
        environmentDefaultIAMRoleName=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )


@pytest.fixture(scope="module", autouse=True)
def target_environment_group(environment_group: Callable, target_environment: models.Environment,
                             group2: models.Group) -> models.EnvironmentGroup:
    yield environment_group(
        environment=target_environment,
        group=group2
    )


@pytest.fixture(scope="module", autouse=True)
def dataset1(dataset: Callable, org1: models.Organization, source_environment: models.Environment) -> models.Dataset:
    yield dataset(
        organization=org1,
        environment=source_environment,
        label="dataset1"
    )


@pytest.fixture(scope="module", autouse=True)
def table1(table: Callable, dataset1: models.Dataset) -> models.DatasetTable:
    yield table(
        dataser=dataset1,
        label="table1"
    )


@pytest.fixture(scope="module", autouse=True)
def share_same_account(
        share: Callable, dataset1: models.Dataset, source_environment: models.Environment,
        source_environment_group_requesters: models.EnvironmentGroup) -> models.ShareObject:
    yield share(
        dataset=dataset1,
        environment=source_environment,
        env_group=source_environment_group_requesters
    )


@pytest.fixture(scope="module", autouse=True)
def share_cross_account(
        share: Callable, dataset1: models.Dataset, target_environment_group: models.EnvironmentGroup
                        ) -> models.ShareObject:
    yield share(
        dataset=dataset1,
        environment=target_environment,
        env_group=target_environment_group
    )


@pytest.fixture(scope="module", autouse=True)
def share_item_same_account(share_item_table: Callable, share_same_account: models.ShareObject,
                            table1: models.DatasetTable) -> models.ShareObjectItem:
    yield share_item_table(
        share=share_same_account,
        table=table1
    )

@pytest.fixture(scope="module", autouse=True)
def share_item_cross_account(share_item_table: Callable, share_cross_account: models.ShareObject,
                             table1: models.DatasetTable) -> models.ShareObjectItem:
    yield share_item_table(
        share=share_cross_account,
        table=table1
    )

@pytest.fixture(scope="module", autouse=True)
def processor_cross_account(db):
    with db.scoped_session() as session:
        processor = ProcessLFCrossAccountShare(
            session,
            dataset1,
            share_cross_account,
            [table1],
            [],
            source_environment,
            target_environment,
            target_environment_group,
        )
    yield processor

@pytest.fixture(scope="module", autouse=True)
def processor_same_account(db):
    with db.scoped_session() as session:
        processor = ProcessLFSameAccountShare(
            session,
            dataset1,
            share_same_account,
            [table1],
            [],
            source_environment,
            source_environment,
            source_environment_group_requesters,
        )
    yield processor


def test_build_shared_db_name(
        db,
        shared_db_name: str
):
    # Given a dataset and its share, build db_share name
    # Then, it should return
    assert processor_same_account.build_shared_db_name() == (dataset1.GlueDatabaseName + '_shared_' + share_same_account.shareUri)[:254]
    assert processor_cross_account.build_shared_db_name() == (dataset1.GlueDatabaseName + '_shared_' + share_cross_account.shareUri)[:254]


def test_get_share_principals(
        db,
        share_principals: [str]
):
    # Given a dataset and its share, build db_share name
    # Then, it should return
    assert processor_same_account.get_share_principals() == [f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_same_account.principalIAMRoleName}"]
    assert processor_cross_account.get_share_principals() == [f"arn:aws:iam::{source_environment.AwsAccountId}:role/{share_cross_account.principalIAMRoleName}"]


def test_create_shared_database(
        db,
        shared_db_name: str,
        share_principals: [str],
        mocker,
):
    create_db_mock = mocker.patch(
        "dataall.aws.handlers.glue.Glue.create_database",
        return_value=True,
    )
    lf_mock_pr = mocker.patch(
        "dataall.aws.handlers.lakeformation.LakeFormation.grant_pivot_role_all_database_permissions",
        return_value=True,
    )
    lf_mock = mocker.patch(
        "dataall.aws.handlers.lakeformation.LakeFormation.grant_permissions_to_database",
        return_value=True,
    )
    # When
    processor_same_account.create_shared_database()

    # Then
    create_db_mock.assert_called_once()
    lf_mock_pr.assert_called_once()
    lf_mock.assert_called_once()

    # Reset mocks
    create_db_mock.reset_mock()
    lf_mock_pr.reset_mock()
    lf_mock.reset_mock()

    # When
    processor_cross_account.create_shared_database()

    # Then
    create_db_mock.assert_called_once()
    lf_mock_pr.assert_called_once()
    lf_mock.assert_called_once()


# def test_handle_share_failure(
#     mocker,
#     source_environment_group: models.EnvironmentGroup,
#     target_environment_group: models.EnvironmentGroup,
#     dataset1: models.Dataset,
#     db,
#     share1: models.ShareObject,
#     share_item_folder1: models.ShareObjectItem,
#     location1: models.DatasetStorageLocation,
#     source_environment: models.Environment,
#     target_environment: models.Environment,
# ):
#     # Given
#     alarm_service_mock = mocker.patch.object(AlarmService, "trigger_folder_sharing_failure_alarm")
#
#     with db.scoped_session() as session:
#         manager = S3ShareManager(
#             session,
#             dataset1,
#             share1,
#             location1,
#             source_environment,
#             target_environment,
#             source_environment_group,
#             target_environment_group,
#         )
#
#         error = Exception
#         # When
#         manager.handle_share_failure(error)
#
#         # Then
#         alarm_service_mock.assert_called()
#
#
# def test_handle_revoke_failure(
#     mocker,
#     source_environment_group: models.EnvironmentGroup,
#     target_environment_group: models.EnvironmentGroup,
#     dataset1: models.Dataset,
#     db,
#     share1: models.ShareObject,
#     share_item_folder1: models.ShareObjectItem,
#     location1: models.DatasetStorageLocation,
#     source_environment: models.Environment,
#     target_environment: models.Environment,
# ):
#     # Given
#     alarm_service_mock = mocker.patch.object(AlarmService, "trigger_revoke_folder_sharing_failure_alarm")
#
#     with db.scoped_session() as session:
#         manager = S3ShareManager(
#             session,
#             dataset1,
#             share1,
#             location1,
#             source_environment,
#             target_environment,
#             source_environment_group,
#             target_environment_group,
#         )
#
#         error = Exception
#         # When
#         manager.handle_revoke_failure(error)
#
#         # Then
#         alarm_service_mock.assert_called()
