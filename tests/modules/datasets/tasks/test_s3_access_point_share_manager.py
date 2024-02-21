from unittest.mock import MagicMock

import pytest
import json

from typing import Callable

from dataall.core.groups.db.group_models import Group
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup, ConsumptionRole
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.dataset_sharing.aws.s3_client import S3ControlClient
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject, ShareObjectItem

from dataall.modules.dataset_sharing.services.share_managers import S3AccessPointShareManager
from dataall.modules.datasets_base.db.dataset_models import DatasetStorageLocation, Dataset

SOURCE_ENV_ACCOUNT = "111111111111"
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"

TARGET_ACCOUNT_ENV = "222222222222"
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"

DATAALL_ACCESS_POINT_KMS_DECRYPT_SID = "DataAll-Access-Point-KMS-Decrypt"
DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID = "KMSPivotRolePermissions"


@pytest.fixture(scope="module")
def source_environment(env: Callable, org_fixture: Organization, group: Group):
    source_environment = env(
        org=org_fixture,
        account=SOURCE_ENV_ACCOUNT,
        envname="source_environment",
        owner=group.owner,
        group=group.name,
        role=SOURCE_ENV_ROLE_NAME,
    )
    yield source_environment


@pytest.fixture(scope="module")
def source_environment_group(environment_group: Callable, source_environment: Environment, group: Group):
    source_environment_group = environment_group(source_environment, group.name)
    yield source_environment_group


@pytest.fixture(scope="module")
def target_environment(env: Callable, org_fixture: Organization, group2: Group):
    target_environment = env(
        org=org_fixture,
        account=TARGET_ACCOUNT_ENV,
        envname="target_environment",
        owner=group2.owner,
        group=group2.name,
        role=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )
    yield target_environment


@pytest.fixture(scope="module")
def target_environment_group(environment_group: Callable, target_environment: Environment, group2: Group):
    target_environment_group = environment_group(target_environment, group2.name)
    yield target_environment_group


@pytest.fixture(scope="module")
def dataset1(create_dataset: Callable, org_fixture: Organization, source_environment: Environment):
    dataset1 = create_dataset(org_fixture, source_environment, "dataset1")
    yield dataset1


@pytest.fixture(scope="module")
def location1(location: Callable, dataset1: Dataset) -> DatasetStorageLocation:
    yield location(dataset1, "location1")


@pytest.fixture(scope="module")
def share1(share: Callable, dataset1: Dataset,
           target_environment: Environment,
           target_environment_group: EnvironmentGroup) -> ShareObject:
    share1 = share(dataset1, target_environment, target_environment_group)
    yield share1


@pytest.fixture(scope="module")
def share_item_folder1(share_item_folder: Callable, share1: ShareObject, location1: DatasetStorageLocation):
    share_item_folder1 = share_item_folder(share1, location1)
    return share_item_folder1


@pytest.fixture(scope="module")
def base_bucket_policy():
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Principal": {"AWS": "*"},
                "Action": "s3:*",
                "Resource": ["arn:aws:s3:::dataall-iris-test-120922-4s47wv71",
                             "arn:aws:s3:::dataall-iris-test-120922-4s47wv71/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
                "Action": "s3:*",
                "Resource": "arn:aws:s3:::dataall-iris-test-120922-4s47wv71",
            },
        ],
    }
    return bucket_policy


@pytest.fixture(scope="module")
def admin_ap_delegation_bucket_policy():
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Principal": {"AWS": "*"},
                "Action": "s3:*",
                "Resource": ["arn:aws:s3:::dataall-iris-test-120922-4s47wv71",
                             "arn:aws:s3:::dataall-iris-test-120922-4s47wv71/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
                "Action": "s3:*",
                "Resource": "arn:aws:s3:::dataall-iris-test-120922-4s47wv71",
            },
            {
                "Sid": "DelegateAccessToAccessPoint",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": ["arn:aws:s3:::bucket-name", "arn:aws:s3:::bucket-name/*"],
                "Condition": {"StringLike": {"aws:userId": "11111"}},
            },
        ],
    }

    return bucket_policy


def mock_s3_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_access_point_share_manager.S3Client',
        mock_client
    )
    mock_client.create_bucket_policy.return_value = None
    return mock_client


def mock_s3_control_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_access_point_share_manager.S3ControlClient',
        mock_client
    )

    mock_client.delete_bucket_access_point.return_value = None
    mock_client.attach_access_point_policy.return_value = None

    # original call
    mock_client.generate_access_point_policy_template.side_effect = \
        S3ControlClient.generate_access_point_policy_template

    return mock_client


def mock_kms_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_access_point_share_manager.KmsClient',
        mock_client
    )
    mock_client.put_key_policy.return_value = None
    return mock_client


def mock_iam_client(mocker, account_id, role_name):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_access_point_share_manager.IAM',
        mock_client
    )
    mock_client.get_role_arn_by_name.return_value = f"arn:aws:iam::{account_id}:role/{role_name}"
    return mock_client


@pytest.fixture(scope="module")
def target_dataset_access_control_policy(request):
    iam_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [
                    f"arn:aws:s3:::{request.param[0]}",
                    f"arn:aws:s3:::{request.param[0]}/*",
                    f"arn:aws:s3:datasetregion:{request.param[1]}:accesspoint/{request.param[2]}",
                    f"arn:aws:s3:datasetregion:{request.param[1]}:accesspoint/{request.param[2]}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112"
                ]
            }
        ],
    }

    return iam_policy


def test_manage_bucket_policy_no_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset1,
        db,
        share1: ShareObject,
        share_item_folder1,
        location1,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy,
):
    # Given
    bucket_policy = base_bucket_policy
    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_delegation_role_arn",
        return_value="arn:role",
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_ids",
        return_value=[1, 2, 3],
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.manage_bucket_policy()

        created_bucket_policy = json.loads(
            s3_client().create_bucket_policy.call_args.args[1]
        )

        # Then
        print(f"Bucket policy generated {created_bucket_policy}")

        sid_list = [statement.get("Sid") for statement in
                    created_bucket_policy["Statement"] if statement.get("Sid")]

        assert "AllowAllToAdmin" in sid_list
        assert "DelegateAccessToAccessPoint" in sid_list


def test_manage_bucket_policy_existing_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset1,
        db,
        share1: ShareObject,
        share_item_folder1,
        location1,
        source_environment: Environment,
        target_environment: Environment,
        admin_ap_delegation_bucket_policy,
):
    # Given
    bucket_policy = admin_ap_delegation_bucket_policy
    s3_client = mock_s3_client(mocker)

    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.manage_bucket_policy()

        # Then
        s3_client.create_bucket_policy.assert_not_called()


@pytest.mark.parametrize("target_dataset_access_control_policy",
                         ([("bucketname", "aws_account_id", "access_point_name")]),
                         indirect=True)
def test_grant_target_role_access_policy_existing_policy_bucket_not_included(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset1,
        db,
        share1: ShareObject,
        share_item_folder1,
        location1,
        source_environment: Environment,
        target_environment: Environment,
        target_dataset_access_control_policy,
):
    # Given
    iam_policy = target_dataset_access_control_policy

    mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1', iam_policy))

    iam_update_role_policy_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.update_managed_policy_default_version",
        return_value=None,
    )

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.grant_target_role_access_policy()

        # Then
        iam_update_role_policy_mock.assert_called()

        # Iam function is called with str from object so we transform back to object
        policy_object = iam_policy

        # Assert that bucket_name is inside the resource array of policy object
        assert location1.S3BucketName in ",".join(policy_object["Statement"][0]["Resource"])
        assert f"arn:aws:kms:{dataset1.region}:{dataset1.AwsAccountId}:key/kms-key" in \
               iam_policy["Statement"][1]["Resource"] \
               and "kms:*" in iam_policy["Statement"][1]["Action"]


@pytest.mark.parametrize("target_dataset_access_control_policy", ([("dataset1", SOURCE_ENV_ACCOUNT, "test")]),
                         indirect=True)
def test_grant_target_role_access_policy_existing_policy_bucket_included(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset1,
        db,
        share1: ShareObject,
        share_item_folder1,
        location1,
        source_environment: Environment,
        target_environment: Environment,
        target_dataset_access_control_policy,
):
    # Given
    iam_policy = target_dataset_access_control_policy

    mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1', iam_policy))

    iam_update_role_policy_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.update_managed_policy_default_version",
        return_value=None,
    )

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.grant_target_role_access_policy()

        # Then
        iam_update_role_policy_mock.assert_called()


def test_grant_target_role_access_policy_test_no_policy(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):

    initial_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "arn:aws:s3:::initial-fake-empty-bucket",
                ]
            }
        ]
    }

    # Given
    mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',initial_policy_document))


    iam_update_role_policy_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.update_managed_policy_default_version",
        return_value=None,
    )

    expected_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [
                    f"arn:aws:s3:::{location1.S3BucketName}",
                    f"arn:aws:s3:::{location1.S3BucketName}/*",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{share_item_folder1.S3AccessPointName}",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{share_item_folder1.S3AccessPointName}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:{dataset1.region}:{dataset1.AwsAccountId}:key/kms-key"
                ]
            }
        ],
    }

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.grant_target_role_access_policy()

        expected_policy_name = ConsumptionRole.generate_policy_name(target_environment.environmentUri,
                                                                    share1.principalIAMRoleName)
        # Then
        iam_update_role_policy_mock.assert_called_with(
            target_environment.AwsAccountId, expected_policy_name,
            "v1", json.dumps(expected_policy)
        )


def test_update_dataset_bucket_key_policy_with_env_admin(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = None
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share1.principalIAMRoleName)

    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_ACCESS_POINT_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        "env_admin_arn"
                    ]
                },
                "Action": "kms:Decrypt",
                "Resource": "*",
            }
        ],
    }

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        # When
        manager.update_dataset_bucket_key_policy()

        # Then
        kms_client().put_key_policy.assert_called()


def _generate_ap_policy_object(
        access_point_arn: str,
        env_admin_prefix_list: list,
):
    new_ap_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowAllToAdmin",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": "access-point-arn",
                "Condition": {"StringLike": {"aws:userId": ["dataset_admin_role_id:*", "source_env_admin_role_id:*",
                                                            "source_account_pivot_role_id:*"]}},
            },
        ],
    }

    for statement in env_admin_prefix_list:
        first_half = {
            "Sid": f"{statement[0]}0",
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:ListBucket",
            "Resource": f"{access_point_arn}",
            "Condition": {"StringLike": {"s3:prefix": [], "aws:userId": [f"{statement[0]}"]}},
        }
        second_half = {
            "Sid": f"{statement[0]}1",
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:GetObject",
            "Resource": [],
            "Condition": {"StringLike": {"aws:userId": [f"{statement[0]}:*"]}},
        }
        prefix_list = []
        for prefix in statement[1]:
            prefix_list.append(f"{prefix}/*")
            second_half["Resource"].append(f"{access_point_arn}/object/{prefix}/*")

        if len(prefix_list) > 1:
            first_half["Condition"]["StringLike"]["s3:prefix"] = prefix_list
        else:
            first_half["Condition"]["StringLike"]["s3:prefix"] = prefix_list[0]

        new_ap_policy["Statement"].append(first_half)
        new_ap_policy["Statement"].append(second_half)

    return new_ap_policy


def test_update_dataset_bucket_key_policy_without_env_admin(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share1.principalIAMRoleName)

    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": DATAALL_ACCESS_POINT_KMS_DECRYPT_SID,
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        "different_env_admin_id"
                    ]
                },
                "Action": "kms:Decrypt",
                "Resource": "*"
            }
        ],
    }

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        # When
        manager.update_dataset_bucket_key_policy()

        kms_client().put_key_policy.assert_called()

        # Check the modified KMS key policy
        kms_key_policy = json.loads(kms_client().put_key_policy.call_args[0][1])

        # Then
        assert len(kms_key_policy["Statement"]) == 2
        assert kms_key_policy["Statement"][0]["Sid"] == DATAALL_ACCESS_POINT_KMS_DECRYPT_SID
        assert kms_key_policy["Statement"][0]["Action"] == "kms:Decrypt"

        # Check if the "Principal" contains the added target_requester_arn
        assert "Principal" in kms_key_policy["Statement"][0]
        assert "AWS" in kms_key_policy["Statement"][0]["Principal"]
        assert "different_env_admin_id" in kms_key_policy["Statement"][0]["Principal"]["AWS"]
        assert kms_key_policy["Statement"][0]["Resource"] == "*"  # Resource should be "*"
        assert f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}" in \
               kms_key_policy["Statement"][0]["Principal"]["AWS"]


# NO existing Access point and ap policy
def test_manage_access_point_and_policy_1(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    access_point_arn = "new-access-point-arn"
    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().create_bucket_access_point.return_value = access_point_arn
    s3_control_client().get_bucket_access_point_arn.return_value = access_point_arn
    s3_control_client().get_access_point_policy.return_value = None

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_ids",
        return_value=["dataset_admin_role_id:*", "source_env_admin_role_id:*" "source_account_pivot_role_id:*"],
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_delegation_role_arn",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.manage_access_point_and_policy()

        # Then
        s3_control_client().attach_access_point_policy.assert_called()
        policy = s3_control_client().attach_access_point_policy.call_args.kwargs.get('policy')
        new_ap_policy = json.loads(policy)

        # Asser that access point is in resource
        assert new_ap_policy["Statement"][0]["Resource"] == access_point_arn

        # Assert that listbucket and getobject permissions were added for target environment admin
        assert "s3:GetObject" in [
            statement["Action"] for statement in new_ap_policy["Statement"] if
            statement["Sid"].startswith(target_environment.SamlGroupName)
        ]
        assert "s3:ListBucket" in [
            statement["Action"] for statement in new_ap_policy["Statement"] if
            statement["Sid"].startswith(target_environment.SamlGroupName)
        ]

        # Assert AllowAllToAdmin "Sid" exists
        assert len([statement for statement in new_ap_policy["Statement"] if statement["Sid"] == "AllowAllToAdmin"]) > 0


# Existing Access point and ap policy
# target_env_admin is already in policy
# current folder is NOT yet in prefix_list
def test_manage_access_point_and_policy_2(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given

    # Existing access point
    access_point_arn = "existing-access-point-arn"
    s3_client = mock_s3_control_client(mocker)
    s3_client().get_bucket_access_point_arn.return_value = access_point_arn

    # target_env_admin is already in policy but current folder is NOT yet in prefix_list
    existing_ap_policy = _generate_ap_policy_object(access_point_arn,
                                                    [[target_environment.SamlGroupName, ["existing-prefix"]]])

    # Existing access point policy
    s3_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.manage_access_point_and_policy()

        # Then
        s3_client().attach_access_point_policy.assert_called()
        policy = s3_client().attach_access_point_policy.call_args.kwargs.get('policy')

        # Assert S3 Prefix of share folder in prefix_list
        new_ap_policy = json.loads(policy)
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}
        prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"]["s3:prefix"]

        assert f"{location1.S3Prefix}/*" in prefix_list

        # Assert s3 prefix is in resource_list
        resource_list = statements[f"{target_environment.SamlGroupName}1"]["Resource"]

        assert f"{access_point_arn}/object/{location1.S3Prefix}/*" in resource_list


# Existing Access point and ap policy
# target_env_admin is NOT already in ap policy
# current folder is NOT yet in prefix_list
def test_manage_access_point_and_policy_3(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given

    # Existing access point
    access_point_arn = "existing-access-point-arn"
    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().get_bucket_access_point_arn.return_value = access_point_arn

    # New target env admin and prefix are not in existing ap policy
    existing_ap_policy = _generate_ap_policy_object(access_point_arn, [["another-env-admin", ["existing-prefix"]]])

    # Existing access point policy
    s3_control_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.manage_access_point_and_policy()

        # Then
        s3_control_client().attach_access_point_policy.assert_called()

        # Assert S3 Prefix of share folder in prefix_list
        policy = s3_control_client().attach_access_point_policy.call_args.kwargs.get('policy')
        new_ap_policy = json.loads(policy)
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}
        prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"]["s3:prefix"]

        assert f"{location1.S3Prefix}/*" in prefix_list

        # Assert s3 prefix is in resource_list
        resource_list = statements[f"{target_environment.SamlGroupName}1"]["Resource"]

        assert f"{access_point_arn}/object/{location1.S3Prefix}/*" in resource_list


def test_delete_access_point_policy_with_env_admin_one_prefix(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given

    # Existing access point
    access_point_arn = "existing-access-point-arn"
    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().get_bucket_access_point_arn.return_value = access_point_arn

    # New target env admin and prefix are already in existing ap policy
    # Another admin is part of this policy
    existing_ap_policy = _generate_ap_policy_object(
        access_point_arn,
        [[target_environment.SamlGroupName, [location1.S3Prefix]], ["another-env-admin", [location1.S3Prefix]]],
    )

    s3_control_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)
    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_access_point_policy()

        # Then
        s3_control_client().attach_access_point_policy.assert_called()

        # Assert statements for share have been removed
        new_ap_policy = json.loads(s3_control_client().attach_access_point_policy.call_args.kwargs.get('policy'))
        deleted_statements = {item["Sid"]: item for item in new_ap_policy["Statement"] if
                              item["Sid"].startswith(f"{target_environment.SamlGroupName}")}

        assert len(deleted_statements) == 0

        # Assert other statements are remaining
        remaining_statements = {item["Sid"]: item for item in new_ap_policy["Statement"] if
                                not item["Sid"].startswith(f"{target_environment.SamlGroupName}")}

        assert len(remaining_statements) > 0


def test_delete_access_point_policy_with_env_admin_multiple_prefix(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given

    access_point_arn = "existing-access-point-arn"
    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().get_bucket_access_point_arn.return_value = access_point_arn

    existing_ap_policy = _generate_ap_policy_object(
        access_point_arn,
        [[target_environment.SamlGroupName, [location1.S3Prefix, "another-prefix"]],
         ["another-env-admin", [location1.S3Prefix]]],
    )

    s3_control_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)
    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_access_point_policy()

        # Then
        s3_control_client().attach_access_point_policy.assert_called()

        # Assert statements for share have been removed
        new_ap_policy = json.loads(s3_control_client().attach_access_point_policy.call_args.kwargs.get('policy'))
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}

        remaining_prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"][
            "s3:prefix"]

        assert location1.S3Prefix not in remaining_prefix_list
        assert "another-prefix/*" in remaining_prefix_list


def test_dont_delete_access_point_with_policy(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    existing_ap_policy = _generate_ap_policy_object("access-point-arn",
                                                    [[target_environment.SamlGroupName, ["existing-prefix"]]])

    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)
    # When
    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        is_deleted = manager.delete_access_point(share1, dataset1)

        # Then
        assert not is_deleted
        assert not s3_control_client().delete_bucket_access_point.called


def test_delete_access_point_without_policy(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given ap policy that only includes AllowAllToAdminStatement
    existing_ap_policy = _generate_ap_policy_object("access-point-arn", [])

    s3_control_client = mock_s3_control_client(mocker)
    s3_control_client().get_access_point_policy.return_value = json.dumps(existing_ap_policy)
    s3_control_client().delete_bucket_access_point.return_value = None

    # When
    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        is_deleted = manager.delete_access_point(share1, dataset1)

        # Then
        assert is_deleted
        assert s3_control_client().delete_bucket_access_point.called


def test_delete_target_role_access_policy_no_remaining_statement(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given ap policy that only includes AllowAllToAdminStatement
    existing_target_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [
                    f"arn:aws:s3:::{location1.S3BucketName}",
                    f"arn:aws:s3:::{location1.S3BucketName}/*",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3AccessPointShareManager.build_access_point_name(share1)}",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3AccessPointShareManager.build_access_point_name(share1)}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:{dataset1.region}:{dataset1.AwsAccountId}:key/kms-key"
                ]
            }
        ],
    }

    initial_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "arn:aws:s3:::initial-fake-empty-bucket",
                ]
            }
        ]
    }

    # Given
    mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',existing_target_role_policy))


    iam_update_role_policy_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.update_managed_policy_default_version",
        return_value=None,
    )


    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    # When
    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_target_role_access_policy(share1, dataset1, target_environment)

        expected_policy_name = ConsumptionRole.generate_policy_name(target_environment.environmentUri,
                                                                    share1.principalIAMRoleName)

        iam_update_role_policy_mock.assert_called_with(
            target_environment.AwsAccountId, expected_policy_name,
            "v1", json.dumps(initial_policy_document)
        )


def test_delete_target_role_access_policy_with_remaining_statement(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    # target role policy that has a bucket unrelated to the current bucket to be deleted
    existing_target_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [
                    "arn:aws:s3:::UNRELATED_BUCKET_ARN",
                    f"arn:aws:s3:::{location1.S3BucketName}",
                    f"arn:aws:s3:::{location1.S3BucketName}/*",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3AccessPointShareManager.build_access_point_name(share1)}",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3AccessPointShareManager.build_access_point_name(share1)}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112",
                    f"arn:aws:kms:{dataset1.region}:{dataset1.AwsAccountId}:key/kms-key"
                ]
            }
        ],
    }

    expected_remaining_target_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": ["arn:aws:s3:::UNRELATED_BUCKET_ARN"],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112"
                ]
            }
        ],
    }

    # Given
    mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',existing_target_role_policy))


    iam_update_role_policy_mock = mocker.patch(
        "dataall.base.aws.iam.IAM.update_managed_policy_default_version",
        return_value=None,
    )

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    # When
    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_target_role_access_policy(share1, dataset1, target_environment)

        # Then
        expected_policy_name = ConsumptionRole.generate_policy_name(target_environment.environmentUri,
                                                                    share1.principalIAMRoleName)

        iam_update_role_policy_mock.assert_called_with(
            target_environment.AwsAccountId, expected_policy_name,
            "v1", json.dumps(expected_remaining_target_role_policy)
        )


# The kms key policy includes the target env admin to be removed aswell as one additional target env
# admin, that should remain
def test_delete_dataset_bucket_key_policy_existing_policy_with_additional_target_env(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "1"
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share1.principalIAMRoleName)

    # Includes target env admin to be removed and another, that should remain
    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_ACCESS_POINT_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    "SomeTargetResourceArn",
                    f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share1.principalIAMRoleName}"
                ]},
                "Action": "kms:Decrypt",
                "Resource": "*"
            }
        ],
    }

    remaining_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_ACCESS_POINT_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    "SomeTargetResourceArn"
                ]},
                "Action": "kms:Decrypt",
                "Resource": "*"
            }
        ],
    }

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_dataset_bucket_key_policy(dataset1)

        # Then
        kms_client().put_key_policy.assert_called()
        kms_client().put_key_policy.assert_called_with(
            kms_client().get_key_id.return_value,
            json.dumps(remaining_policy)
        )


# The kms key policy only includes the target env admin
def test_delete_dataset_bucket_key_policy_existing_policy_with_no_additional_target_env(
        mocker,
        source_environment_group: EnvironmentGroup,
        target_environment_group: EnvironmentGroup,
        dataset1: Dataset,
        db,
        share1: ShareObject,
        share_item_folder1: ShareObjectItem,
        location1: DatasetStorageLocation,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "1"
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share1.principalIAMRoleName)

    # Includes target env admin to be removed and another, that should remain
    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_ACCESS_POINT_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    f"arn:aws:iam::{target_environment.AwsAccountId}:role/{share1.principalIAMRoleName}"
                ]},
                "Action": "kms:Decrypt",
                "Resource": "*"
            },
            {
                "Sid": f"{DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    f"arn:aws:iam::{target_environment.AwsAccountId}:role/dataallPivotRole"
                ]},
                "Action": [
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:GenerateDataKey*",
                    "kms:PutKeyPolicy",
                    "kms:GetKeyPolicy",
                    "kms:ReEncrypt*",
                    "kms:TagResource",
                    "kms:UntagResource"
                ],
                "Resource": "*"
            }
        ],
    }

    remaining_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    f"arn:aws:iam::{target_environment.AwsAccountId}:role/dataallPivotRole"
                ]},
                "Action": [
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:GenerateDataKey*",
                    "kms:PutKeyPolicy",
                    "kms:GetKeyPolicy",
                    "kms:ReEncrypt*",
                    "kms:TagResource",
                    "kms:UntagResource"
                ],
                "Resource": "*"
            }
        ],
    }

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)

    with db.scoped_session() as session:
        manager = S3AccessPointShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # When
        manager.delete_dataset_bucket_key_policy(dataset1)

        # Then
        kms_client().put_key_policy.assert_called()
        kms_client().put_key_policy.assert_called_with(
            kms_client().get_key_id.return_value,
            json.dumps(remaining_policy)
        )
