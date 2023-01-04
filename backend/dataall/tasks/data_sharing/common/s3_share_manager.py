import logging
import json


from ....db import models, api
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.s3 import S3
from ....aws.handlers.kms import KMS
from ....aws.handlers.iam import IAM

from ....utils.alarm_service import AlarmService

logger = logging.getLogger(__name__)


class S3ShareManager:
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        target_folder: models.DatasetStorageLocation,
        source_environment: models.Environment,
        target_environment: models.Environment,
        source_env_group: models.EnvironmentGroup,
        env_group: models.EnvironmentGroup,
    ):
        self.session = session
        self.source_env_group = source_env_group
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.target_folder = target_folder
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.share_item = api.ShareObject.find_share_item_by_folder(
            session,
            share,
            target_folder,
        )
        self.access_point_name = self.share_item.S3AccessPointName

        self.source_account_id = dataset.AwsAccountId
        self.target_account_id = target_environment.AwsAccountId
        self.source_env_admin = source_env_group.environmentIAMRoleArn
        self.target_requester_IAMRoleName = share.principalIAMRoleName
        self.bucket_name = target_folder.S3BucketName
        self.dataset_admin = dataset.IAMDatasetAdminRoleArn
        self.dataset_account_id = dataset.AwsAccountId
        self.dataset_region = dataset.region
        self.s3_prefix = target_folder.S3Prefix

    def manage_bucket_policy(self):
        """
        This function will manage bucket policy by grant admin access to dataset admin, pivot role
        and environment admin. All of the policies will only be added once.
        :return:
        """
        logger.info(
            f'Manage Bucket policy for {self.bucket_name}'
        )
        bucket_policy = json.loads(S3.get_bucket_policy(self.source_account_id, self.source_environment.region, self.bucket_name))
        for statement in bucket_policy["Statement"]:
            if statement.get("Sid") in ["AllowAllToAdmin", "DelegateAccessToAccessPoint"]:
                return
        exceptions_roleId = [f'{item}:*' for item in SessionHelper.get_role_ids(
            self.source_account_id,
            [self.dataset_admin, self.source_env_admin, SessionHelper.get_delegation_role_arn(self.source_account_id)]
        )]
        allow_owner_access = {
            "Sid": "AllowAllToAdmin",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{self.bucket_name}",
                f"arn:aws:s3:::{self.bucket_name}/*"
            ],
            "Condition": {
                "StringLike": {
                    "aws:userId": exceptions_roleId
                }
            }
        }
        delegated_to_accesspoint = {
            "Sid": "DelegateAccessToAccessPoint",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{self.bucket_name}",
                f"arn:aws:s3:::{self.bucket_name}/*"
            ],
            "Condition": {
                "StringEquals": {
                    "s3:DataAccessPointAccount": f"{self.source_account_id}"
                }
            }
        }
        bucket_policy["Statement"].append(allow_owner_access)
        bucket_policy["Statement"].append(delegated_to_accesspoint)
        S3.create_bucket_policy(self.source_account_id, self.source_environment.region, self.bucket_name, json.dumps(bucket_policy))

    def grant_target_role_access_policy(self):
        """
        Updates requester IAM role policy to include requested S3 bucket and access point
        :return:
        """
        logger.info(
            f'Grant target role {self.target_requester_IAMRoleName} access policy'
        )
        existing_policy = IAM.get_role_policy(
            self.target_account_id,
            self.target_requester_IAMRoleName,
            "targetDatasetAccessControlPolicy",
        )
        if existing_policy:  # type dict
            if self.bucket_name not in ",".join(existing_policy["Statement"][0]["Resource"]):
                logger.info(
                    f'targetDatasetAccessControlPolicy exists for IAM role {self.target_requester_IAMRoleName}, '
                    f'but S3 Access point {self.access_point_name} is not included, updating...'
                )
                target_resources = [
                    f"arn:aws:s3:::{self.bucket_name}",
                    f"arn:aws:s3:::{self.bucket_name}/*",
                    f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}",
                    f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}/*"
                ]
                policy = existing_policy["Statement"][0]["Resource"].extend(target_resources)
            else:
                logger.info(
                    f'targetDatasetAccessControlPolicy exists for IAM role {self.target_requester_IAMRoleName} '
                    f'and S3 Access point {self.access_point_name} is included, skipping...'
                )
                return
        else:
            logger.info(
                f'targetDatasetAccessControlPolicy does not exists for IAM role {self.target_requester_IAMRoleName}, creating...'
            )
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:*"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{self.bucket_name}",
                            f"arn:aws:s3:::{self.bucket_name}/*",
                            f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}",
                            f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}/*"
                        ]
                    }
                ]
            }
        IAM.update_role_policy(
            self.target_account_id,
            self.target_requester_IAMRoleName,
            "targetDatasetAccessControlPolicy",
            json.dumps(policy),
        )

    def manage_access_point_and_policy(self):
        """
        :return:
        """

        access_point_arn = S3.get_bucket_access_point_arn(self.source_account_id, self.source_environment.region, self.access_point_name)
        if not access_point_arn:
            logger.info(
                'Access point does not exists, creating...'
            )
            access_point_arn = S3.create_bucket_access_point(self.source_account_id, self.source_environment.region, self.bucket_name, self.access_point_name)
        existing_policy = S3.get_access_point_policy(self.source_account_id, self.source_environment.region, self.access_point_name)
        # requester will use this role to access resources
        target_requester_id = SessionHelper.get_role_id(self.target_account_id, self.target_requester_IAMRoleName)
        if existing_policy:
            # Update existing access point policy
            logger.info(
                f'There is already an existing access point {access_point_arn} with an existing policy, updating policy...'
            )
            existing_policy = json.loads(existing_policy)
            statements = {item["Sid"]: item for item in existing_policy["Statement"]}
            if f"{target_requester_id}0" in statements.keys():
                prefix_list = statements[f"{target_requester_id}0"]["Condition"]["StringLike"]["s3:prefix"]
                if isinstance(prefix_list, str):
                    prefix_list = [prefix_list]
                if f"{self.s3_prefix}/*" not in prefix_list:
                    prefix_list.append(f"{self.s3_prefix}/*")
                    statements[f"{target_requester_id}0"]["Condition"]["StringLike"]["s3:prefix"] = prefix_list
                resource_list = statements[f"{target_requester_id}1"]["Resource"]
                if isinstance(resource_list, str):
                    resource_list = [resource_list]
                if f"{access_point_arn}/object/{self.s3_prefix}/*" not in resource_list:
                    resource_list.append(f"{access_point_arn}/object/{self.s3_prefix}/*")
                    statements[f"{target_requester_id}1"]["Resource"] = resource_list
                existing_policy["Statement"] = list(statements.values())
            else:
                additional_policy = S3.generate_access_point_policy_template(
                    target_requester_id,
                    access_point_arn,
                    self.s3_prefix,
                )
                existing_policy["Statement"].extend(additional_policy["Statement"])
            access_point_policy = existing_policy
        else:
            # First time to create access point policy
            logger.info(
                f'Access point policy for access point {access_point_arn} does not exists, creating policy...'
            )
            access_point_policy = S3.generate_access_point_policy_template(
                target_requester_id,
                access_point_arn,
                self.s3_prefix,
            )
            exceptions_roleId = [f'{item}:*' for item in SessionHelper.get_role_ids(
                self.source_account_id,
                [self.dataset_admin, self.source_env_admin, SessionHelper.get_delegation_role_arn(self.source_account_id)]
            )]
            admin_statement = {
                "Sid": "AllowAllToAdmin",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": f"{access_point_arn}",
                "Condition": {
                    "StringLike": {
                        "aws:userId": exceptions_roleId
                    }
                }
            }
            access_point_policy["Statement"].append(admin_statement)
        S3.attach_access_point_policy(self.source_account_id, self.source_environment.region, self.access_point_name, json.dumps(access_point_policy))

    def update_dataset_bucket_key_policy(self):
        logger.info(
            'Updating dataset Bucket KMS key policy...'
        )
        key_alias = f"alias/{self.dataset.KmsAlias}"
        kms_keyId = KMS.get_key_id(self.source_account_id, self.source_environment.region, key_alias)
        existing_policy = KMS.get_key_policy(self.source_account_id, self.source_environment.region, kms_keyId, "default")
        target_requester_id = SessionHelper.get_role_id(self.target_account_id, self.target_requester_IAMRoleName)
        if existing_policy and f'{target_requester_id}:*' not in existing_policy:
            policy = json.loads(existing_policy)
            policy["Statement"].append(
                {
                    "Sid": f"{target_requester_id}",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "kms:Decrypt",
                    "Resource": "*",
                    "Condition": {
                        "StringLike": {
                            "aws:userId": f"{target_requester_id}:*"
                        }
                    }
                }
            )
            KMS.put_key_policy(
                self.source_account_id,
                self.source_environment.region,
                kms_keyId,
                "default",
                json.dumps(policy)
            )

    def delete_access_point_policy(self):
        logger.info(
            f'Deleting access point policy for access point {self.access_point_name}...'
        )
        access_point_policy = json.loads(S3.get_access_point_policy(self.source_account_id, self.source_environment.region, self.access_point_name))
        access_point_arn = S3.get_bucket_access_point_arn(self.source_account_id, self.source_environment.region, self.access_point_name)
        target_requester_id = SessionHelper.get_role_id(self.target_account_id, self.target_requester_IAMRoleName)
        statements = {item["Sid"]: item for item in access_point_policy["Statement"]}
        if f"{target_requester_id}0" in statements.keys():
            prefix_list = statements[f"{target_requester_id}0"]["Condition"]["StringLike"]["s3:prefix"]
            if isinstance(prefix_list, list) and f"{self.s3_prefix}/*" in prefix_list:
                prefix_list.remove(f"{self.s3_prefix}/*")
                statements[f"{target_requester_id}1"]["Resource"].remove(f"{access_point_arn}/object/{self.s3_prefix}/*")
                access_point_policy["Statement"] = list(statements.values())
            else:
                access_point_policy["Statement"].remove(statements[f"{target_requester_id}0"])
                access_point_policy["Statement"].remove(statements[f"{target_requester_id}1"])
        S3.attach_access_point_policy(self.source_account_id, self.source_environment.region, self.access_point_name, json.dumps(access_point_policy))

    def delete_access_point(self):
        logger.info(
            f'Deleting access point {self.access_point_name}...'
        )
        access_point_policy = json.loads(S3.get_access_point_policy(self.source_account_id, self.source_environment.region, self.access_point_name))
        if len(access_point_policy["Statement"]) <= 1:
            # At least we have the 'AllowAllToAdmin' statement
            S3.delete_bucket_access_point(self.source_account_id, self.source_environment.region, self.access_point_name)
            return True
        else:
            return False

    def delete_target_role_access_policy(self):
        logger.info(
            'Deleting target role IAM policy...'
        )
        existing_policy = IAM.get_role_policy(
            self.target_account_id,
            self.target_requester_IAMRoleName,
            "targetDatasetAccessControlPolicy",
        )
        if existing_policy:
            if self.bucket_name in ",".join(existing_policy["Statement"][0]["Resource"]):
                target_resources = [
                    f"arn:aws:s3:::{self.bucket_name}",
                    f"arn:aws:s3:::{self.bucket_name}/*",
                    f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}",
                    f"arn:aws:s3:{self.dataset_region}:{self.dataset_account_id}:accesspoint/{self.access_point_name}/*"
                ]
                for item in target_resources:
                    existing_policy["Statement"][0]["Resource"].remove(item)
                if not existing_policy["Statement"][0]["Resource"]:
                    IAM.delete_role_policy(self.target_account_id, self.target_requester_IAMRoleName, "targetDatasetAccessControlPolicy")
                else:
                    IAM.update_role_policy(
                        self.target_account_id,
                        self.target_requester_IAMRoleName,
                        "targetDatasetAccessControlPolicy",
                        json.dumps(existing_policy),
                    )

    def delete_dataset_bucket_key_policy(self):
        logger.info(
            'Deleting dataset bucket KMS key policy...'
        )
        key_alias = f"alias/{self.dataset.KmsAlias}"
        kms_keyId = KMS.get_key_id(self.source_account_id, self.source_environment.region, key_alias)
        existing_policy = KMS.get_key_policy(self.source_account_id, self.source_environment.region, kms_keyId, "default")
        target_requester_id = SessionHelper.get_role_id(self.target_account_id, self.target_requester_IAMRoleName)
        if existing_policy and f'{target_requester_id}:*' in existing_policy:
            policy = json.loads(existing_policy)
            policy["Statement"] = [item for item in policy["Statement"] if item["Sid"] != f"{target_requester_id}"]
            KMS.put_key_policy(
                self.source_account_id,
                self.source_environment.region,
                kms_keyId,
                "default",
                json.dumps(policy)
            )

    def handle_share_failure(self, error: Exception) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Returns
        -------
        True if alarm published successfully
        """
        logger.error(
            f'Failed to share folder {self.s3_prefix} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            self.share_item,
            models.ShareObjectStatus.Share_Failed.value,
        )
        AlarmService().trigger_folder_sharing_failure_alarm(
            self.target_folder, self.share, self.target_environment
        )
        return True

    def handle_revoke_failure(self, error: Exception) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Returns
        -------
        True if alarm published successfully
        """
        logger.error(
            f'Failed to revoke S3 permissions to folder {self.s3_prefix} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            self.share_item,
            models.ShareObjectStatus.Revoke_Share_Failed.value,
        )
        AlarmService().trigger_revoke_folder_sharing_failure_alarm(
            self.target_folder, self.share, self.target_environment
        )
        return True
