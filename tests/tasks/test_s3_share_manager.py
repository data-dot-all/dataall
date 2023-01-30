import pytest
import json

from typing import Callable

from dataall.db import models

from dataall.tasks.data_sharing.share_managers.s3_share_manager import S3ShareManager
from dataall.utils.alarm_service import AlarmService


SOURCE_ENV_ACCOUNT = "111111111111"
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"


TARGET_ACCOUNT_ENV = "222222222222"
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"


@pytest.fixture(scope="module")
def org1(org: Callable) -> models.Organization:
    org1 = org(label="org", owner="alice", SamlGroupName="admins")
    yield org1


@pytest.fixture(scope="module")
def source_environment(environment: Callable, org1: models.Organization, group: models.Group):
    source_environment = environment(
        organization=org1,
        awsAccountId=SOURCE_ENV_ACCOUNT,
        label="source_environment",
        owner=group.owner,
        samlGroupName=group.name,
        environmentDefaultIAMRoleName=SOURCE_ENV_ROLE_NAME,
    )
    yield source_environment


@pytest.fixture(scope="module")
def source_environment_group(environment_group: Callable, source_environment: models.Environment, group: models.Group):
    source_environment_group = environment_group(source_environment, group)
    yield source_environment_group


@pytest.fixture(scope="module")
def target_environment(environment: Callable, org1: models.Organization, group2: models.Group):
    target_environment = environment(
        organization=org1,
        awsAccountId=TARGET_ACCOUNT_ENV,
        label="target_environment",
        owner=group2.owner,
        samlGroupName=group2.name,
        environmentDefaultIAMRoleName=TARGET_ACCOUNT_ENV_ROLE_NAME,
    )
    yield target_environment


@pytest.fixture(scope="module")
def target_environment_group(environment_group: Callable, target_environment: models.Environment, group2: models.Group):
    target_environment_group = environment_group(target_environment, group2)
    yield target_environment_group


@pytest.fixture(scope="module")
def dataset1(dataset: Callable, org1: models.Organization, source_environment: models.Environment):
    dataset1 = dataset(org1, source_environment, "dataset1")
    yield dataset1


@pytest.fixture(scope="module")
def location1(location: Callable, dataset1: models.Dataset) -> models.DatasetStorageLocation:
    yield location(dataset1, "location1")


@pytest.fixture(scope="module")
def share1(share: Callable, dataset1: models.Dataset, 
           target_environment: models.Environment,
           target_environment_group: models.EnvironmentGroup) -> models.ShareObject:
    share1 = share(dataset1, target_environment, target_environment_group)
    yield share1


@pytest.fixture(scope="module")
def share_item_folder1(share_item_folder: Callable, share1: models.ShareObject, location1: models.DatasetStorageLocation):
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
                "Resource": ["arn:aws:s3:::dataall-iris-test-120922-4s47wv71", "arn:aws:s3:::dataall-iris-test-120922-4s47wv71/*"],
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
                "Resource": ["arn:aws:s3:::dataall-iris-test-120922-4s47wv71", "arn:aws:s3:::dataall-iris-test-120922-4s47wv71/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
                "Action": "s3:*",
                "Resource": "arn:aws:s3:::dataall-iris-test-120922-4s47wv71",
            },
            {
                "Sid": "AllowAllToAdmin",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": ["arn:aws:s3:::bucket-name", "arn:aws:s3:::bucket-name/*"],
                "Condition": {"StringLike": {"aws:userId": "11111"}},
            },
        ],
    }

    return bucket_policy


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
    share1: models.ShareObject,
    share_item_folder1,
    location1,
    source_environment: models.Environment,
    target_environment: models.Environment,
    base_bucket_policy,
):

    # Given
    bucket_policy = base_bucket_policy

    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_policy",
        return_value=json.dumps(bucket_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_delegation_role_arn",
        return_value="arn:role",
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_ids",
        return_value=[1, 2, 3],
    )

    s3_create_bucket_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.create_bucket_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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

        created_bucket_policy = json.loads(s3_create_bucket_mock.call_args.args[3])

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
    share1: models.ShareObject,
    share_item_folder1,
    location1,
    source_environment: models.Environment,
    target_environment: models.Environment,
    admin_ap_delegation_bucket_policy,
):

    # Given
    bucket_policy = admin_ap_delegation_bucket_policy

    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_policy",
        return_value=json.dumps(bucket_policy),
    )

    s3_create_bucket_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.create_bucket_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_create_bucket_mock.assert_not_called()


@pytest.mark.parametrize("target_dataset_access_control_policy", 
                         ([("bucketname", "aws_account_id", "access_point_name")]),
                         indirect=True)
def test_grant_target_role_access_policy_existing_policy_bucket_not_included(
    mocker,
    source_environment_group,
    target_environment_group,
    dataset1,
    db,
    share1: models.ShareObject,
    share_item_folder1,
    location1,
    source_environment: models.Environment,
    target_environment: models.Environment,
    target_dataset_access_control_policy,
):

    # Given
    iam_policy = target_dataset_access_control_policy

    mocker.patch(
        "dataall.aws.handlers.iam.IAM.get_role_policy",
        return_value=iam_policy,
    )

    iam_update_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.update_role_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        policy_object = json.loads(iam_update_role_policy_mock.call_args.args[3])

        # Assert that bucket_name is inside the resource array of policy object
        assert location1.S3BucketName in ",".join(policy_object["Statement"][0]["Resource"])


@pytest.mark.parametrize("target_dataset_access_control_policy", ([("dataset1", SOURCE_ENV_ACCOUNT, "test")]), indirect=True)
def test_grant_target_role_access_policy_existing_policy_bucket_included(
    mocker,
    source_environment_group,
    target_environment_group,
    dataset1,
    db,
    share1: models.ShareObject,
    share_item_folder1,
    location1,
    source_environment: models.Environment,
    target_environment: models.Environment,
    target_dataset_access_control_policy,
):

    # Given
    iam_policy = target_dataset_access_control_policy

    mocker.patch(
        "dataall.aws.handlers.iam.IAM.get_role_policy",
        return_value=iam_policy,
    )

    iam_update_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.update_role_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        iam_update_role_policy_mock.assert_not_called()


def test_grant_target_role_access_policy_test_no_policy(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):

    # Given
    mocker.patch(
        "dataall.aws.handlers.iam.IAM.get_role_policy",
        return_value=None,
    )

    iam_update_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.update_role_policy",
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
            }
        ],
    }

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        iam_update_role_policy_mock.assert_called_with(
            target_environment.AwsAccountId, share1.principalIAMRoleName, 
            "targetDatasetAccessControlPolicy", json.dumps(expected_policy)
        )


def test_update_dataset_bucket_key_policy_with_env_admin(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_id",
        return_value=None,
    )

    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{target_environment.SamlGroupName}",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": f"{target_environment.SamlGroupName}:*"}},
            }
        ],
    }

    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_policy",
        return_value=json.dumps(existing_key_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    kms_put_key_policy_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.put_key_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        manager.update_dataset_bucket_key_policy()

        # Then
        kms_put_key_policy_mock.assert_not_called()


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
                "Condition": {"StringLike": {"aws:userId": ["dataset_admin_role_id:*", "source_env_admin_role_id:*", "source_account_pivot_role_id:*"]}},
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
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_id",
        return_value="kms-key",
    )

    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "different_env_admin_id",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": "different_env_admin_id:*"}},
            }
        ],
    }

    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_policy",
        return_value=json.dumps(existing_key_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    new_key_policy = {
        "Sid": f"{target_environment.SamlGroupName}",
        "Effect": "Allow",
        "Principal": {"AWS": "*"},
        "Action": "kms:Decrypt",
        "Resource": "*",
        "Condition": {"StringLike": {"aws:userId": f"{target_environment.SamlGroupName}:*"}},
    }

    kms_put_key_policy_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.put_key_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        manager.update_dataset_bucket_key_policy()

        existing_key_policy["Statement"].append(new_key_policy)

        expected_complete_key_policy = existing_key_policy

        # Then
        kms_put_key_policy_mock.assert_called_with(source_environment.AwsAccountId, "eu-central-1", "kms-key", "default", json.dumps(expected_complete_key_policy))


# NO existing Access point and ap policy
def test_manage_access_point_and_policy_1(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_access_point_arn",
        return_value=None,
    )

    s3_create_bucket_access_point_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.create_bucket_access_point",
        return_value="new-access-point-arn",
    )

    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=None,
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_ids",
        return_value=["dataset_admin_role_id:*", "source_env_admin_role_id:*" "source_account_pivot_role_id:*"],
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_delegation_role_arn",
        return_value=None,
    )

    s3_attach_access_point_policy_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.attach_access_point_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_attach_access_point_policy_mock.assert_called()
        policy = s3_attach_access_point_policy_mock.call_args.kwargs.get('policy')
        new_ap_policy = json.loads(policy)

        # Asser that access point is in resource
        assert new_ap_policy["Statement"][0]["Resource"] == s3_create_bucket_access_point_mock.return_value

        # Assert that listbucket and getobject permissions were added for target environment admin
        assert "s3:ListBucket" in [
            statement["Action"] for statement in new_ap_policy["Statement"] if statement["Sid"].startswith(target_environment.SamlGroupName)
        ]
        assert "s3:GetObject" in [
            statement["Action"] for statement in new_ap_policy["Statement"] if statement["Sid"].startswith(target_environment.SamlGroupName)
        ]

        # Assert AllowAllToAdmin "Sid" exists
        assert len([statement for statement in new_ap_policy["Statement"] if statement["Sid"] == "AllowAllToAdmin"]) > 0


# Existing Access point and ap policy
# target_env_admin is already in policy
# current folder is NOT yet in prefix_list
def test_manage_access_point_and_policy_2(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given

    # Existing access point
    s3_get_bucket_access_point_arn_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_access_point_arn",
        return_value="existing-access-point-arn",
    )

    # target_env_admin is already in policy but current folder is NOT yet in prefix_list
    existing_ap_policy = _generate_ap_policy_object(s3_get_bucket_access_point_arn_mock.return_value, [[target_environment.SamlGroupName, ["existing-prefix"]]])

    # Existing access point policy
    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    s3_attach_access_point_policy_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.attach_access_point_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_attach_access_point_policy_mock.assert_called()
        policy = s3_attach_access_point_policy_mock.call_args.kwargs.get('policy')

        # Assert S3 Prefix of share folder in prefix_list
        new_ap_policy = json.loads(policy)
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}
        prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"]["s3:prefix"]

        assert f"{location1.S3Prefix}/*" in prefix_list

        # Assert s3 prefix is in resource_list
        resource_list = statements[f"{target_environment.SamlGroupName}1"]["Resource"]

        assert f"{s3_get_bucket_access_point_arn_mock.return_value}/object/{location1.S3Prefix}/*" in resource_list


# Existing Access point and ap policy
# target_env_admin is NOT already in ap policy
# current folder is NOT yet in prefix_list
def test_manage_access_point_and_policy_3(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given

    # Existing access point
    s3_get_bucket_access_point_arn_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_access_point_arn",
        return_value="existing-access-point-arn",
    )

    # New target env admin and prefix are not in existing ap policy
    existing_ap_policy = _generate_ap_policy_object(s3_get_bucket_access_point_arn_mock.return_value, [["another-env-admin", ["existing-prefix"]]])

    # Existing access point policy
    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    s3_attach_access_point_policy_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.attach_access_point_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_attach_access_point_policy_mock.assert_called()

        # Assert S3 Prefix of share folder in prefix_list
        policy = s3_attach_access_point_policy_mock.call_args.kwargs.get('policy')
        new_ap_policy = json.loads(policy)
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}
        prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"]["s3:prefix"]

        assert f"{location1.S3Prefix}/*" in prefix_list

        # Assert s3 prefix is in resource_list
        resource_list = statements[f"{target_environment.SamlGroupName}1"]["Resource"]

        assert f"{s3_get_bucket_access_point_arn_mock.return_value}/object/{location1.S3Prefix}/*" in resource_list


def test_delete_access_point_policy_with_env_admin_one_prefix(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given

    # Existing access point
    s3_get_bucket_access_point_arn_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_access_point_arn",
        return_value="existing-access-point-arn",
    )

    # New target env admin and prefix are already in existing ap policy
    # Another admin is part of this policy
    existing_ap_policy = _generate_ap_policy_object(
        s3_get_bucket_access_point_arn_mock.return_value,
        [[target_environment.SamlGroupName, [location1.S3Prefix]], ["another-env-admin", [location1.S3Prefix]]],
    )

    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    s3_attach_access_point_policy_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.attach_access_point_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_attach_access_point_policy_mock.assert_called()

        # Assert statements for share have been removed
        new_ap_policy = json.loads(s3_attach_access_point_policy_mock.call_args.args[3])
        deleted_statements = {item["Sid"]: item for item in new_ap_policy["Statement"] if item["Sid"].startswith(f"{target_environment.SamlGroupName}")}

        assert len(deleted_statements) == 0

        # Assert other statements are remaining
        remaining_statements = {item["Sid"]: item for item in new_ap_policy["Statement"] if not item["Sid"].startswith(f"{target_environment.SamlGroupName}")}

        assert len(remaining_statements) > 0


def test_delete_access_point_policy_with_env_admin_multiple_prefix(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given

    s3_get_bucket_access_point_arn_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_bucket_access_point_arn",
        return_value="existing-access-point-arn",
    )

    existing_ap_policy = _generate_ap_policy_object(
        s3_get_bucket_access_point_arn_mock.return_value,
        [[target_environment.SamlGroupName, [location1.S3Prefix, "another-prefix"]], ["another-env-admin", [location1.S3Prefix]]],
    )

    mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    s3_attach_access_point_policy_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.attach_access_point_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        s3_attach_access_point_policy_mock.assert_called()

        # Assert statements for share have been removed
        new_ap_policy = json.loads(s3_attach_access_point_policy_mock.call_args.args[3])
        statements = {item["Sid"]: item for item in new_ap_policy["Statement"]}

        remaining_prefix_list = statements[f"{target_environment.SamlGroupName}0"]["Condition"]["StringLike"]["s3:prefix"]

        assert location1.S3Prefix not in remaining_prefix_list
        assert "another-prefix/*" in remaining_prefix_list


def test_dont_delete_access_point_with_policy(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    existing_ap_policy = _generate_ap_policy_object("access-point-arn", [[target_environment.SamlGroupName, ["existing-prefix"]]])

    s3_delete_bucket_access_point_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    s3_delete_bucket_access_point_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.delete_bucket_access_point",
        return_value=None,
    )

    # When
    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        assert not s3_delete_bucket_access_point_mock.called


def test_delete_access_point_without_policy(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given ap policy that only includes AllowAllToAdminStatement
    existing_ap_policy = _generate_ap_policy_object("access-point-arn", [])

    s3_delete_bucket_access_point_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.get_access_point_policy",
        return_value=json.dumps(existing_ap_policy),
    )

    s3_delete_bucket_access_point_mock = mocker.patch(
        "dataall.aws.handlers.s3.S3.delete_bucket_access_point",
        return_value=None,
    )

    # When
    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        assert s3_delete_bucket_access_point_mock.called


def test_delete_target_role_access_policy_no_remaining_statement(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
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
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3ShareManager.build_access_point_name(share1)}",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3ShareManager.build_access_point_name(share1)}/*",
                ],
            }
        ],
    }

    mocker.patch(
        "dataall.aws.handlers.iam.IAM.get_role_policy",
        return_value=existing_target_role_policy,
    )

    iam_delete_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.delete_role_policy",
        return_value=None,
    )

    iam_update_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.update_role_policy",
        return_value=None,
    )

    # When
    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        iam_delete_role_policy_mock.assert_called()
        iam_update_role_policy_mock.assert_not_called()


def test_delete_target_role_access_policy_with_remaining_statement(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
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
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3ShareManager.build_access_point_name(share1)}",
                    f"arn:aws:s3:{dataset1.region}:{dataset1.AwsAccountId}:accesspoint/{S3ShareManager.build_access_point_name(share1)}/*",
                ],
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
            }
        ],
    }

    mocker.patch(
        "dataall.aws.handlers.iam.IAM.get_role_policy",
        return_value=existing_target_role_policy,
    )

    iam_delete_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.delete_role_policy",
        return_value=None,
    )

    iam_update_role_policy_mock = mocker.patch(
        "dataall.aws.handlers.iam.IAM.update_role_policy",
        return_value=None,
    )

    # When
    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        iam_delete_role_policy_mock.assert_not_called()

        iam_update_role_policy_mock.assert_called_with(
            target_environment.AwsAccountId,
            share1.principalIAMRoleName,
            "targetDatasetAccessControlPolicy",
            json.dumps(expected_remaining_target_role_policy),
        )


# The kms key policy includes the target env admin to be removed aswell as one additional target env
# admin, that should remain
def test_delete_dataset_bucket_key_policy_existing_policy_with_additional_target_env(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    kms_get_key_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_id",
        return_value="1",
    )

    # Includes target env admin to be removed and another, that should remain
    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{target_environment.SamlGroupName}",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": f"{target_environment.SamlGroupName}:*"}},
            },
            {
                "Sid": "REMAINING_TARGET_ENV_ADMIN_ID",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": "REMAINING_TARGET_ENV_ADMIN_ID:*"}},
            },
        ],
    }

    remaining_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "REMAINING_TARGET_ENV_ADMIN_ID",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": "REMAINING_TARGET_ENV_ADMIN_ID:*"}},
            }
        ],
    }

    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_policy",
        return_value=json.dumps(existing_key_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    kms_put_key_policy_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.put_key_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        manager.delete_dataset_bucket_key_policy(share1, dataset1, target_environment)

        # Then
        kms_put_key_policy_mock.assert_called()
        kms_put_key_policy_mock.assert_called_with(source_environment.AwsAccountId, 'eu-central-1', kms_get_key_mock.return_value, "default", json.dumps(remaining_policy))


# The kms key policy only includes the target env admin
def test_delete_dataset_bucket_key_policy_existing_policy_with_no_additional_target_env(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    kms_get_key_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_id",
        return_value="1",
    )

    # Includes target env admin to be removed and another, that should remain
    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{target_environment.SamlGroupName}",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "kms:Decrypt",
                "Resource": "*",
                "Condition": {"StringLike": {"aws:userId": f"{target_environment.SamlGroupName}:*"}},
            }
        ],
    }

    remaining_policy = {
        "Version": "2012-10-17",
        "Statement": [],
    }

    mocker.patch(
        "dataall.aws.handlers.kms.KMS.get_key_policy",
        return_value=json.dumps(existing_key_policy),
    )

    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_role_id",
        return_value=target_environment.SamlGroupName,
    )

    kms_put_key_policy_mock = mocker.patch(
        "dataall.aws.handlers.kms.KMS.put_key_policy",
        return_value=None,
    )

    with db.scoped_session() as session:
        manager = S3ShareManager(
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
        manager.delete_dataset_bucket_key_policy(share1, dataset1, target_environment)

        # Then
        kms_put_key_policy_mock.assert_called()
        kms_put_key_policy_mock.assert_called_with(source_environment.AwsAccountId, 'eu-central-1', kms_get_key_mock.return_value, "default", json.dumps(remaining_policy))


def test_handle_share_failure(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    alarm_service_mock = mocker.patch.object(AlarmService, "trigger_folder_sharing_failure_alarm")

    with db.scoped_session() as session:
        manager = S3ShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        error = Exception
        # When
        manager.handle_share_failure(error)

        # Then
        alarm_service_mock.assert_called()


def test_handle_revoke_failure(
    mocker,
    source_environment_group: models.EnvironmentGroup,
    target_environment_group: models.EnvironmentGroup,
    dataset1: models.Dataset,
    db,
    share1: models.ShareObject,
    share_item_folder1: models.ShareObjectItem,
    location1: models.DatasetStorageLocation,
    source_environment: models.Environment,
    target_environment: models.Environment,
):
    # Given
    alarm_service_mock = mocker.patch.object(AlarmService, "trigger_revoke_folder_sharing_failure_alarm")

    with db.scoped_session() as session:
        manager = S3ShareManager(
            session,
            dataset1,
            share1,
            location1,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        error = Exception
        # When
        manager.handle_revoke_failure(error)

        # Then
        alarm_service_mock.assert_called()
