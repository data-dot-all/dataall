import pytest
import json
from unittest.mock import MagicMock

from typing import Callable

from dataall.core.groups.db.group_models import Group
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.services.share_managers import S3BucketShareManager
from dataall.modules.dataset_sharing.services.managed_share_policy_service import SharePolicyService
from dataall.modules.datasets_base.db.dataset_models import Dataset, DatasetBucket

SOURCE_ENV_ACCOUNT = "111111111111"
SOURCE_ENV_ROLE_NAME = "dataall-ProducerEnvironment-i6v1v1c2"

TARGET_ACCOUNT_ENV = "222222222222"
TARGET_ACCOUNT_ENV_ROLE_NAME = "dataall-ConsumersEnvironment-r71ucp4m"

DATAALL_READ_ONLY_SID = "DataAll-Bucket-ReadOnly"
DATAALL_ALLOW_ALL_ADMINS_SID = "AllowAllToAdmin"

DATAALL_BUCKET_KMS_DECRYPT_SID = "DataAll-Bucket-KMS-Decrypt"
DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID = "KMSPivotRolePermissions"

IAM_S3_ACCESS_POINTS_STATEMENT_SID = "AccessPointsStatement"
IAM_S3_BUCKETS_STATEMENT_SID = "BucketStatement"
EMPTY_STATEMENT_SID = "EmptyStatement"

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
def dataset_imported(create_dataset: Callable, org_fixture: Organization, source_environment: Environment):
    dataset_imported = create_dataset(org_fixture, source_environment, "dataset_imported", True)
    yield dataset_imported


@pytest.fixture(scope="module")
def dataset2(create_dataset: Callable, org_fixture: Organization, source_environment: Organization):
    dataset2 = create_dataset(org_fixture, source_environment, "dataset2")
    yield dataset2


@pytest.fixture(scope="module")
def bucket2(bucket: Callable, dataset2: Dataset) -> DatasetBucket:
    yield bucket(dataset2, "bucket2")


@pytest.fixture(scope="module")
def bucket3(bucket: Callable, dataset_imported: Dataset) -> DatasetBucket:
    yield bucket(dataset_imported, "bucket3")


@pytest.fixture(scope="module")
def share2(share: Callable, dataset2: Dataset,
           target_environment: Environment,
           target_environment_group: EnvironmentGroup) -> ShareObject:
    share2 = share(dataset2, target_environment, target_environment_group)
    yield share2


@pytest.fixture(scope="module")
def share3(share: Callable, dataset_imported: Dataset,
           target_environment: Environment,
           target_environment_group: EnvironmentGroup) -> ShareObject:
    share3 = share(dataset_imported, target_environment, target_environment_group)
    yield share3


@pytest.fixture(scope="function")
def base_bucket_policy(dataset2):
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Principal": {"AWS": "*"},
                "Action": "s3:*",
                "Resource": [f"arn:aws:s3:::{dataset2.S3BucketName}", f"arn:aws:s3:::{dataset2.S3BucketName}/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            }
        ],
    }
    return bucket_policy


def base_kms_key_policy(target_requester_arn=None):
    if target_requester_arn is None:
        target_requester_arn = f"arn:aws:iam::{TARGET_ACCOUNT_ENV}:role/{TARGET_ACCOUNT_ENV_ROLE_NAME}"

    kms_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_BUCKET_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    f"{target_requester_arn}"
                ]},
                "Action": "kms:Decrypt",
                "Resource": "*"
            },
            {
                "Sid": f"{DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}",
                "Effect": "Allow",
                "Principal": {"AWS": [
                    f"arn:aws:iam::{TARGET_ACCOUNT_ENV}:role/dataallPivotRole"
                ]},
                "Action": [
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:GenerateDataKey*",
                    "kms:PutKeyPolicy",
                    "kms:GetKeyPolicy",
                    "kms:ReEncrypt*",
                    "kms:TagResource",
                    "kms:UntagResource",
                ],
                "Resource": "*"
            }
        ],
    }
    return kms_policy


def complete_access_bucket_policy(target_requester_arn, s3_bucket_name, owner_roleId):
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Principal": {
                    "AWS": "*"
                },
                "Sid": "RequiredSecureTransport",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{s3_bucket_name}",
                    f"arn:aws:s3:::{s3_bucket_name}/*"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            },
            {
                "Sid": f"{DATAALL_ALLOW_ALL_ADMINS_SID}",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{s3_bucket_name}",
                    f"arn:aws:s3:::{s3_bucket_name}/*"
                ],
                "Condition": {
                    "StringLike": {
                        "aws:userId": owner_roleId
                    }
                }
            },
            {
                "Sid": f"{DATAALL_READ_ONLY_SID}",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        f"{target_requester_arn}"
                    ]
                },
                "Action": [
                    "s3:List*",
                    "s3:GetObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{s3_bucket_name}",
                    f"arn:aws:s3:::{s3_bucket_name}/*"
                ]
            }
        ]
    }

    return bucket_policy


def mock_s3_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_bucket_share_manager.S3Client',
        mock_client
    )
    mock_client.create_bucket_policy.return_value = None
    return mock_client


def mock_kms_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_bucket_share_manager.KmsClient',
        mock_client
    )
    mock_client.put_key_policy.return_value = None
    return mock_client


def mock_iam_client(mocker, account_id, role_name):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.dataset_sharing.services.share_managers.s3_bucket_share_manager.IAM',
        mock_client
    )
    mock_client.get_role_arn_by_name.return_value = f"arn:aws:iam::{account_id}:role/{role_name}"
    return mock_client


# For below test cases, dataset2, share2, src, target env and src group , env group remain the same
def test_grant_role_bucket_policy_with_no_policy_present(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        bucket2,
        db,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given
    # No Bucket policy. A Default bucket policy should be formed with DataAll-Bucket-ReadOnly, AllowAllToAdmin & RequiredSecureTransport Sids
    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = None
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_delegation_role_arn",
        return_value="arn:role",
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_ids",
        return_value=[1, 2, 3],
    )

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        # Get the Bucket Policy and it should be the same
        modified_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])
        # Check all the Sids are present
        # Check that the S3 bucket resources are also present
        assert f"{DATAALL_ALLOW_ALL_ADMINS_SID}" in modified_bucket_policy["Statement"][0]["Sid"]
        assert modified_bucket_policy["Statement"][0]["Resource"] == [f'arn:aws:s3:::{dataset2.S3BucketName}',
                                                                      f'arn:aws:s3:::{dataset2.S3BucketName}/*']
        assert modified_bucket_policy["Statement"][0]["Condition"]["StringLike"]["aws:userId"] == ['1:*', '2:*', '3:*']
        assert "RequiredSecureTransport" in modified_bucket_policy["Statement"][1]["Sid"]
        assert modified_bucket_policy["Statement"][1]["Resource"] == [f'arn:aws:s3:::{dataset2.S3BucketName}',
                                                                      f'arn:aws:s3:::{dataset2.S3BucketName}/*']
        assert f"{DATAALL_READ_ONLY_SID}" in modified_bucket_policy["Statement"][2]["Sid"]
        assert modified_bucket_policy["Statement"][2]["Resource"] == [f'arn:aws:s3:::{dataset2.S3BucketName}',
                                                                      f'arn:aws:s3:::{dataset2.S3BucketName}/*']
        assert modified_bucket_policy["Statement"][2]["Principal"]["AWS"] == [
            f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"]


def test_grant_role_bucket_policy_with_default_complete_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given
    # Bucket Policy containing required "AllowAllToAdmin" and "DataAll-Bucket-ReadOnly" Sid's
    # Bucket Policy shouldn't be modified after calling "grant_role_bucket_policy" function

    target_arn = f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"

    bucket_policy = complete_access_bucket_policy(target_arn,
                                                  dataset2.S3BucketName, "ABNCSJ81982393")

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        # Get the Bucket Policy and it should be the same
        created_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])

        # Check if nothing is removed from the policy and is the policy remains the same
        for policy in created_bucket_policy["Statement"]:
            assert policy["Sid"] in json.dumps(bucket_policy)


def test_grant_role_bucket_policy_with_policy_and_no_allow_owner_sid_and_no_read_only_sid(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        share2: ShareObject,
        bucket2,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy
):
    # Given
    # base bucket policy
    # Check if both "AllowAllToAdmin" and "DataAll-Bucket-ReadOnly" Sid's Statements are added to the policy

    bucket_policy = base_bucket_policy

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_delegation_role_arn",
        return_value="arn:role",
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_ids",
        return_value=[1, 2, 3],
    )

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        # Get the Bucket Policy
        modified_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])

        # AllowToAdmin, DataAll-Bucket-ReadOnly Sid's should be attached now
        for policy in modified_bucket_policy["Statement"]:
            if "Sid" in policy:
                assert policy["Sid"] in [f"{DATAALL_ALLOW_ALL_ADMINS_SID}", f"{DATAALL_READ_ONLY_SID}"]


def test_grant_role_bucket_policy_with_another_read_only_role(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        share2: ShareObject,
        bucket2,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy
):
    # Given base bucket policy with "DataAll-Bucket-ReadOnly"
    bucket_policy = base_bucket_policy

    target_arn = f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"

    # Append a policy for read only role
    bucket_policy["Statement"].append(
        {
            "Sid": f"{DATAALL_READ_ONLY_SID}",
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "SomeTargetResourceArn"
                ]
            },
            "Action": [
                "s3:List*",
                "s3:GetObject"
            ],
            "Resource": [
                f"arn:aws:s3:::someS3Bucket",
                f"arn:aws:s3:::someS3Bucket/*"
            ]
        })

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_delegation_role_arn",
        return_value="arn:role",
    )

    mocker.patch(
        "dataall.base.aws.sts.SessionHelper.get_role_ids",
        return_value=[1, 2, 3],
    )

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        # Get the Bucket Policy and it should be the same
        modified_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])

        # AllowToAdmin Sid should be attached now. Also DataAll-Bucket-ReadOnly Sid should be present
        for policy in modified_bucket_policy["Statement"]:
            if "Sid" in policy:
                assert policy["Sid"] in [f"{DATAALL_ALLOW_ALL_ADMINS_SID}", f"{DATAALL_READ_ONLY_SID}"]

        # Check if the principal was appended and not overridden into the DataAll-Bucket-ReadOnly
        assert len(modified_bucket_policy["Statement"][1]["Principal"]["AWS"]) == 2
        assert modified_bucket_policy["Statement"][1]["Principal"]["AWS"][0] == "SomeTargetResourceArn"


def test_grant_s3_iam_access_with_no_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given
    # There is not existing IAM policy in the requesters account for the dataset's S3bucket
    # Check if the update_role_policy func is called and policy statements are added

    mocker.patch("dataall.base.aws.iam.IAM.get_role_policy", return_value=None)
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"


    initial_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": EMPTY_STATEMENT_SID,
                "Effect": "Allow",
                "Action": "none:null",
                "Resource": "*"
            }
        ]
    }

    iam_update_role_policy_mock_1 = mocker.patch("dataall.base.aws.iam.IAM.update_managed_policy_default_version", return_value=None)
    iam_update_role_policy_mock_2 = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',initial_policy_document))

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_s3_iam_access()

        iam_update_role_policy_mock_1.assert_called()
        iam_update_role_policy_mock_2.assert_called()

        iam_policy = initial_policy_document

        s3_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}S3")
        kms_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS")


        # Assert if the IAM role policy with S3 and KMS permissions was created
        assert len(iam_policy["Statement"]) == 2
        assert len(iam_policy["Statement"][s3_index]["Resource"]) == 2
        assert len(iam_policy["Statement"][kms_index]["Resource"]) == 1
        assert f"arn:aws:s3:::{dataset2.S3BucketName}" in iam_policy["Statement"][s3_index]["Resource"] and "s3:*" in \
               iam_policy["Statement"][s3_index]["Action"]
        assert f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key" in \
               iam_policy["Statement"][kms_index]["Resource"] \
               and "kms:*" in iam_policy["Statement"][kms_index]["Action"]


def test_grant_s3_iam_access_with_policy_and_target_resources_not_present(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given policy with some other bucket as resource
    # Check if the correct resource is attached/appended

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::S3Bucket",
                    f"arn:aws:s3:::S3Bucket/*"
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:12121121121:key/some-kms-key"
                ]
            }
        ]
    }

    mocker.patch("dataall.base.aws.iam.IAM.get_role_policy", return_value=policy)
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    s3_index = SharePolicyService._get_statement_by_sid(policy=policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}S3")
    kms_index = SharePolicyService._get_statement_by_sid(policy=policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS")

    assert len(policy["Statement"]) == 2
    assert len(policy["Statement"][s3_index]["Resource"]) == 2
    assert len(policy["Statement"][kms_index]["Resource"]) == 1

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    iam_update_role_policy_mock = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',policy))

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_s3_iam_access()

        iam_update_role_policy_mock.assert_called()

        iam_policy = policy

        # Assert that new resources were appended
        assert len(policy["Statement"]) == 2
        assert len(iam_policy["Statement"][s3_index]["Resource"]) == 4
        assert f'arn:aws:s3:::{dataset2.S3BucketName}' in iam_policy["Statement"][s3_index]["Resource"]
        assert len(iam_policy["Statement"][kms_index]["Resource"]) == 2
        assert f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key" in iam_policy["Statement"][kms_index][
            "Resource"]


# Tests to check if
def test_grant_s3_iam_access_with_complete_policy_present(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given complete policy present with required target resources
    # Check if policy created after calling function and the existing Policy is same

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::{dataset2.S3BucketName}",
                    f"arn:aws:s3:::{dataset2.S3BucketName}/*"
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::S3Bucket",
                    f"arn:aws:s3:::S3Bucket/*"
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key"
                ]
            }
        ]
    }

    mocker.patch("dataall.base.aws.iam.IAM.get_role_policy", return_value=policy)
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    iam_update_role_policy_mock = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',policy))

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.grant_s3_iam_access()

        # Assert that the IAM Policy is the same as the existing complete policy
        iam_update_role_policy_mock.assert_called()

        created_iam_policy = policy

        s3_index = SharePolicyService._get_statement_by_sid(policy=policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}S3")
        kms_index = SharePolicyService._get_statement_by_sid(policy=policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS")

        assert len(created_iam_policy["Statement"]) == 3
        assert policy["Statement"][s3_index]["Resource"] == created_iam_policy["Statement"][s3_index]["Resource"] and \
               policy["Statement"][s3_index]["Action"] == created_iam_policy["Statement"][s3_index]["Action"]
        assert policy["Statement"][kms_index]["Resource"] == created_iam_policy["Statement"][kms_index]["Resource"] and \
               policy["Statement"][kms_index]["Action"] == \
               created_iam_policy["Statement"][kms_index]["Action"]


def test_grant_dataset_bucket_key_policy_with_complete_policy_present(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given complete existing policy
    # Check if  KMS.put_key_policy is called
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    existing_key_policy = base_kms_key_policy()

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        manager.grant_dataset_bucket_key_policy()

        kms_client().put_key_policy.assert_called()


def test_grant_dataset_bucket_key_policy_with_target_requester_id_absent(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Mock the KMS client
    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    existing_key_policy = base_kms_key_policy("OtherTargetRequestorArn")

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    # Mock the S3BucketShareManager with the KMS client
    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        manager.grant_dataset_bucket_key_policy()

    # Check if KMS.put_key_policy is called and check if the policy is modified
    kms_client().put_key_policy.assert_called()

    # Check the modified KMS key policy
    kms_key_policy = json.loads(kms_client().put_key_policy.call_args[0][1])

    assert len(kms_key_policy["Statement"]) == 2
    assert kms_key_policy["Statement"][0]["Sid"] == DATAALL_BUCKET_KMS_DECRYPT_SID
    assert kms_key_policy["Statement"][0]["Action"] == "kms:Decrypt"

    # Check if the "Principal" contains the added target_requester_arn
    assert "Principal" in kms_key_policy["Statement"][0]
    assert "AWS" in kms_key_policy["Statement"][0]["Principal"]
    assert "OtherTargetRequestorArn" in kms_key_policy["Statement"][0]["Principal"]["AWS"]
    assert kms_key_policy["Statement"][0]["Resource"] == "*"  # Resource should be "*"


# Test Case to check if the IAM Role is updated
def test_grant_dataset_bucket_key_policy_and_default_bucket_key_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset_imported,
        db,
        share3: ShareObject,
        bucket3,
        source_environment: Environment,
        target_environment: Environment
):
    # Given
    # Dataset is imported and it doesn't have Imported KMS Key
    # Mocking KMS key function - > Check if not called
    # Mocking KMS Tags Functions -> Check if not called

    existing_key_policy = base_kms_key_policy("OtherTargetRequestorArn")

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share3.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset_imported,
            share3,
            bucket3,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # dataset2 should not have importedKey to simulate that while importing the dataset a key was not added
        bucket3.importedKmsKey = False
        session.add(bucket3)

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        manager.grant_dataset_bucket_key_policy()

        # Assert that when a dataset is imported and doesn't have importedKey, kms policy function are not triggered
        kms_client().get_key_policy.assert_not_called()
        kms_client().put_key_policy.assert_not_called()

        bucket3.importedKmsKey = True
        session.add(bucket3)


def test_grant_dataset_bucket_key_policy_with_imported(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset_imported,
        bucket3,
        db,
        share3: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given
    # Dataset is imported and it has Imported KMS Key
    # Mocking KMS key function
    # Mocking KMS Tags Functions
    # Check if the bucket policy is modified and the targetResource is added

    existing_key_policy = base_kms_key_policy("OtherTargetRequestorArn")

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share3.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset_imported,
            share3,
            bucket3,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        mocker.patch(
            "dataall.base.aws.sts.SessionHelper.get_delegation_role_name",
            return_value="dataallPivotRole",
        )

        manager.grant_dataset_bucket_key_policy()

        # Assert that when a dataset is imported and has importedKey
        # policy is fetched and the target requester id SID is attached to it
        kms_client().get_key_policy.assert_called()
        kms_client().put_key_policy.assert_called()
        updated_bucket_policy = json.loads(kms_client().put_key_policy.call_args.args[1])

        assert len(updated_bucket_policy["Statement"]) == 2
        assert updated_bucket_policy["Statement"][0]["Sid"] == DATAALL_BUCKET_KMS_DECRYPT_SID
        assert "OtherTargetRequestorArn" in updated_bucket_policy["Statement"][0]["Principal"]["AWS"]


def test_delete_target_role_bucket_policy_with_no_read_only_sid(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        share2: ShareObject,
        bucket2,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy
):
    # Given
    # Base Bucket Policy with no DataAll-Bucket-ReadOnly Sid
    # S3 function to update bucket policy (create_bucket_policy) should not trigger

    bucket_policy = base_bucket_policy

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_policy()

        s3_client().create_bucket_policy.assert_not_called()


def test_delete_target_role_bucket_policy_with_multiple_principals_in_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy
):
    # Given
    # Base Bucket Policy with DataAll-Bucket-ReadOnly Sid And Multiple Principals
    # Check if the appropriate AWS arn is removed and 'SomeotherArn' is retained

    bucket_policy = base_bucket_policy

    addition_to_policy = {
        "Sid": f"{DATAALL_READ_ONLY_SID}",
        "Effect": "Allow",
        "Principal": {
            "AWS": [
                "SomeotherArn",
                f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"
            ]
        },
        "Action": [
            "s3:List*",
            "s3:GetObject"
        ],
        "Resource": [
            f"arn:aws:s3:::{dataset2.S3BucketName}",
            f"arn:aws:s3:::{dataset2.S3BucketName}/*"
        ]
    }

    bucket_policy["Statement"].append(addition_to_policy)

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        modified_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])

        # Check if the 'DataAll-Bucket-ReadOnly' Sid is still present
        # Check if the 'someOtherArn' is still present and the target arn is removed
        assert modified_bucket_policy["Statement"][1]["Sid"] == f"{DATAALL_READ_ONLY_SID}"
        assert len(modified_bucket_policy["Statement"][1]["Principal"]["AWS"]) == 1
        assert 'SomeotherArn' in modified_bucket_policy["Statement"][1]["Principal"]["AWS"]
        assert f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}" not in \
               modified_bucket_policy["Statement"][1]["Principal"]["AWS"]


def test_delete_target_role_bucket_policy_with_one_principal_in_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
        base_bucket_policy
):
    # Given
    # Base Bucket Policy with DataAll-Bucket-ReadOnly Sid And Single target Principals
    # Bucket Policy should not have the DataAll-Bucket-ReadOnly Sid after delete_target_role_bucket_policy is called

    bucket_policy = base_bucket_policy

    addition_to_policy = {
        "Sid": f"{DATAALL_READ_ONLY_SID}",
        "Effect": "Allow",
        "Principal": {
            "AWS": [
                f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"
            ]
        },
        "Action": [
            "s3:List*",
            "s3:GetObject"
        ],
        "Resource": [
            f"arn:aws:s3:::{dataset2.S3BucketName}",
            f"arn:aws:s3:::{dataset2.S3BucketName}/*"
        ]
    }

    bucket_policy["Statement"].append(addition_to_policy)

    assert len(bucket_policy["Statement"]) == 2

    sid_list = [statement["Sid"] for statement in bucket_policy["Statement"] if "Sid" in statement]
    assert f"{DATAALL_READ_ONLY_SID}" in sid_list

    s3_client = mock_s3_client(mocker)
    s3_client().get_bucket_policy.return_value = json.dumps(bucket_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_policy()

        s3_client().create_bucket_policy.assert_called()

        modified_bucket_policy = json.loads(s3_client().create_bucket_policy.call_args.args[1])

        # Check if the 'DataAll-Bucket-ReadOnly' Sid is removed completely
        assert len(modified_bucket_policy["Statement"]) == 1
        sid_list = [statement["Sid"] for statement in modified_bucket_policy["Statement"] if "Sid" in statement]
        assert f"{DATAALL_READ_ONLY_SID}" not in sid_list


def test_delete_target_role_access_policy_no_resource_of_datasets_s3_bucket(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    # IAM Policy which doesn't contain target S3 bucket resources

    iam_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::someOtherBucket",
                    f"arn:aws:s3:::someOtherBucket/*"
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112"
                ]
            }
        ]
    }

    mocker.patch(
        "dataall.base.aws.iam.IAM.get_role_policy",
        return_value=iam_policy,
    )
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    iam_update_role_policy_mock = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',iam_policy))



    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_access_policy(
            share=share2,
            target_bucket=bucket2,
            target_environment=target_environment
        )

        iam_update_role_policy_mock.assert_called()

        # Get the updated IAM policy and compare it with the existing one
        updated_iam_policy = iam_policy
        s3_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}S3")
        kms_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS")


        assert len(updated_iam_policy["Statement"]) == 2
        assert "arn:aws:s3:::someOtherBucket,arn:aws:s3:::someOtherBucket/*" == ",".join(
            updated_iam_policy["Statement"][s3_index]["Resource"])
        assert "arn:aws:kms:us-east-1:121231131212:key/some-key-2112" == ",".join(
            updated_iam_policy["Statement"][kms_index]["Resource"])


def test_delete_target_role_access_policy_with_multiple_s3_buckets_in_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    # IAM Policy with multiple bucket resources along with target environments bucket resources
    # Check if the IAM.update_policy is called and it only updates / deletes the target env bucket resources

    iam_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::someOtherBucket",
                    f"arn:aws:s3:::someOtherBucket/*",
                    f"arn:aws:s3:::{dataset2.S3BucketName}",
                    f"arn:aws:s3:::{dataset2.S3BucketName}/*",
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112",
                    f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key",
                ]
            }
        ]
    }

    mocker.patch(
        "dataall.base.aws.iam.IAM.get_role_policy",
        return_value=iam_policy,
    )
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    iam_update_role_policy_mock = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',iam_policy))


    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_access_policy(
            share=share2,
            target_bucket=bucket2,
            target_environment=target_environment
        )

        iam_update_role_policy_mock.assert_called()

        updated_iam_policy = iam_policy

        s3_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}S3")
        kms_index = SharePolicyService._get_statement_by_sid(policy=iam_policy, sid=f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS")


        assert f"arn:aws:s3:::{dataset2.S3BucketName}" not in updated_iam_policy["Statement"][s3_index]["Resource"]
        assert f"arn:aws:s3:::{dataset2.S3BucketName}/*" not in updated_iam_policy["Statement"][s3_index]["Resource"]
        assert f"arn:aws:s3:::someOtherBucket" in updated_iam_policy["Statement"][s3_index]["Resource"]
        assert f"arn:aws:s3:::someOtherBucket/*" in updated_iam_policy["Statement"][s3_index]["Resource"]

        assert f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key" not in \
               updated_iam_policy["Statement"][kms_index]["Resource"]
        assert f"arn:aws:kms:us-east-1:121231131212:key/some-key-2112" in updated_iam_policy["Statement"][kms_index]["Resource"]


def test_delete_target_role_access_policy_with_one_s3_bucket_and_one_kms_resource_in_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    # IAM Policy with target environments bucket resources only
    # Check if the IAM.delete_policy is called

    iam_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    f"arn:aws:s3:::{dataset2.S3BucketName}",
                    f"arn:aws:s3:::{dataset2.S3BucketName}/*",
                ]
            },
            {
                "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": [
                    f"arn:aws:kms:{dataset2.region}:{dataset2.AwsAccountId}:key/kms-key"
                ]
            }
        ]
    }

    mocker.patch(
        "dataall.base.aws.iam.IAM.get_role_policy",
        return_value=iam_policy,
    )
    mocker.patch("dataall.modules.dataset_sharing.services.managed_share_policy_service.SharePolicyService.check_if_policy_exists", return_value=True)

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    iam_update_role_policy_mock = mocker.patch("dataall.base.aws.iam.IAM.get_managed_policy_default_version", return_value=('v1',iam_policy))


    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_access_policy(
            share=share2,
            target_bucket=bucket2,
            target_environment=target_environment
        )

        iam_update_role_policy_mock.assert_called()


def test_delete_target_role_bucket_key_policy_with_no_target_requester_id(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given
    # complete existing KMS key policy with no target requester id in it
    # Check if KMS.put_key_policy is not called

    existing_key_policy = base_kms_key_policy("Some_other_requester_arn")

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_key_policy(
            target_bucket=bucket2
        )

        kms_client().put_key_policy.assert_not_called()


def test_delete_target_role_bucket_key_policy_with_target_requester_id(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given complete existing KMS key policy with target requester id in it
    # Check if KMS.put_key_policy is called and the statement corresponding to target Sid should be removed

    existing_key_policy = base_kms_key_policy()

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_key_policy(
            target_bucket=bucket2
        )

        kms_client().put_key_policy.assert_called()

        new_kms_policy = json.loads(kms_client().put_key_policy.call_args.args[1])

        assert len(new_kms_policy["Statement"]) == 1


# Test for delete_target_role_bucket_key_policy when dataset is imported
def test_delete_target_role_bucket_key_policy_with_target_requester_id_and_imported_dataset(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset_imported,
        db,
        bucket3,
        share3: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given complete existing KMS key policy with target requester id in it
    # and that the dataset is imported and has a importedKMS key
    # Check if KMS.put_key_policy is called and the statement corresponding to target Sid should be removed

    existing_key_policy = base_kms_key_policy()

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share3.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset_imported,
            share3,
            bucket3,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_key_policy(
            target_bucket=bucket3
        )

        kms_client().put_key_policy.assert_called()

        new_kms_policy = json.loads(kms_client().put_key_policy.call_args.args[1])

        assert len(new_kms_policy["Statement"]) == 1


# Test for delete_target_role_bucket_key_policy when dataset is imported and importedKMS key is missing
def test_delete_target_role_bucket_key_policy_with_target_requester_id_and_imported_dataset_with_no_imported_kms_key(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset_imported,
        db,
        bucket3,
        share3: ShareObject,
        source_environment: Environment,
        target_environment: Environment
):
    # Given complete existing KMS key policy with target requester id in it
    # and the dataset is imported but doens't contain importedKey
    # In that case the KMS.put_key_policy should not be called

    existing_key_policy = base_kms_key_policy()

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share3.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset_imported,
            share3,
            bucket3,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        # dataset2 should not have importedKey to simulate that while importing the dataset a key was not added
        bucket3.importedKmsKey = False
        session.add(dataset_imported)

        manager.delete_target_role_bucket_key_policy(
            target_bucket=bucket3
        )

        kms_client().put_key_policy.assert_not_called()

        bucket3.importedKmsKey = True
        session.add(dataset_imported)


def test_delete_target_role_bucket_key_policy_with_multiple_principals_in_policy(
        mocker,
        source_environment_group,
        target_environment_group,
        dataset2,
        db,
        bucket2,
        share2: ShareObject,
        source_environment: Environment,
        target_environment: Environment,
):
    # Given complete existing KMS key policy with multiple target requester ids
    # Check if KMS.put_key_policy is called and the principal corresponding to target Sid should be removed

    existing_key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": f"{DATAALL_BUCKET_KMS_DECRYPT_SID}",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        "SomeotherArn",
                        f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}"
                    ]
                },
                "Action": "kms:Decrypt",
                "Resource": "*"
            }
        ],
    }

    kms_client = mock_kms_client(mocker)
    kms_client().get_key_id.return_value = "kms-key"

    kms_client().get_key_policy.return_value = json.dumps(existing_key_policy)
    iam_client = mock_iam_client(mocker, target_environment.AwsAccountId, share2.principalIAMRoleName)

    with db.scoped_session() as session:
        manager = S3BucketShareManager(
            session,
            dataset2,
            share2,
            bucket2,
            source_environment,
            target_environment,
            source_environment_group,
            target_environment_group,
        )

        manager.delete_target_role_bucket_key_policy(
            target_bucket=bucket2
        )

        kms_client().put_key_policy.assert_called()

        new_kms_policy = json.loads(kms_client().put_key_policy.call_args.args[1])

        assert new_kms_policy["Statement"][0]["Sid"] == f"{DATAALL_BUCKET_KMS_DECRYPT_SID}"
        assert len(new_kms_policy["Statement"][0]["Principal"]["AWS"]) == 1

        assert 'SomeotherArn' in new_kms_policy["Statement"][0]["Principal"]["AWS"]
        assert f"arn:aws:iam::{target_environment.AwsAccountId}:role/{target_environment.EnvironmentDefaultIAMRoleName}" not in \
               new_kms_policy["Statement"][0]["Principal"]["AWS"]
