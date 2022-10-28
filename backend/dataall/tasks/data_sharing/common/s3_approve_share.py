import logging
import json


from ....db import models, api
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.s3 import S3
from ....aws.handlers.kms import KMS
from ....aws.handlers.iam import IAM

from ....utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class S3ShareApproval:
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        shared_folders: [models.DatasetTable],
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
        self.shared_folders = shared_folders
        self.source_environment = source_environment
        self.target_environment = target_environment

    def approve_share(
            self,
    ) -> bool:
        """
        1) Shares folders, for each shared folder:
            a) ....
        2) Cleans un-shared folders

        Returns
        -------
        True if share is approved successfully
        """
        self.share_folders(
            self.session,
            self.share,
            self.source_env_group,
            self.env_group,
            self.target_environment,
            self.shared_folders,
            self.dataset,
        )

        self.clean_shared_folders(
            self.session,
            self.share,
            self.source_env_group,
            self.env_group,
            self.target_environment,
            self.shared_folders,
            self.dataset,
        )

        return True

    @classmethod
    def share_folders(
        cls,
        session,
        share: models.ShareObject,
        source_env_group: models.EnvironmentGroup,
        target_env_group: models.EnvironmentGroup,
        target_environment: models.Environment,
        shared_folders: [models.DatasetStorageLocation],
        dataset: models.Dataset,
    ):
        for folder in shared_folders:
            share_item = api.ShareObject.find_share_item_by_folder(
                session, share, folder
            )

            api.ShareObject.update_share_item_status(
                session,
                share_item,
                models.ShareObjectStatus.Share_In_Progress.value,
            )

            source_account_id = folder.AWSAccountId
            access_point_name = share_item.S3AccessPointName
            bucket_name = folder.S3BucketName
            target_account_id = target_environment.AwsAccountId
            source_env_admin = source_env_group.environmentIAMRoleArn
            dataset_admin = dataset.IAMDatasetAdminRoleArn
            target_env_admin = target_env_group.environmentIAMRoleName
            s3_prefix = folder.S3Prefix

            try:
                S3ShareApproval.manage_bucket_policy(
                    dataset_admin,
                    source_account_id,
                    bucket_name,
                    source_env_admin,
                )

                S3ShareApproval.grant_target_role_access_policy(
                    bucket_name,
                    access_point_name,
                    target_account_id,
                    target_env_admin,
                    dataset,
                )
                S3ShareApproval.manage_access_point_and_policy(
                    dataset_admin,
                    source_account_id,
                    target_account_id,
                    source_env_admin,
                    target_env_admin,
                    bucket_name,
                    s3_prefix,
                    access_point_name,
                )

                S3ShareApproval.update_dataset_bucket_key_policy(
                    source_account_id,
                    target_account_id,
                    target_env_admin,
                    dataset
                )

                api.ShareObject.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Share_Succeeded.value,
                )
            except Exception as e:
                S3ShareApproval.handle_share_failure(folder, share_item, e)

    @classmethod
    def clean_shared_folders(
        cls,
        session,
        share: models.ShareObject,
        source_env_group: models.EnvironmentGroup,
        target_env_group: models.EnvironmentGroup,
        target_environment: models.Environment,
        dataset: models.Dataset,
        shared_folders: [models.DatasetStorageLocation],
    ):
        source_account_id = dataset.AwsAccountId
        access_point_name = f"{dataset.datasetUri}-{share.principalId}".lower()
        target_account_id = target_environment.AwsAccountId
        target_env_admin = target_env_group.environmentIAMRoleName
        access_point_policy = S3.get_access_point_policy(source_account_id, access_point_name)
        if access_point_policy:
            policy = json.loads(access_point_policy)
            target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
            statements = {item["Sid"]: item for item in policy["Statement"]}
            if f"{target_env_admin_id}0" in statements.keys():
                prefix_list = statements[f"{target_env_admin_id}0"]["Condition"]["StringLike"]["s3:prefix"]
                if isinstance(prefix_list, str):
                    prefix_list = [prefix_list]
                prefix_list = [prefix[:-2] for prefix in prefix_list]
                shared_prefix = [folder.S3Prefix for folder in shared_folders]
                removed_prefixes = [prefix for prefix in prefix_list if prefix not in shared_prefix]
                for prefix in removed_prefixes:
                    bucket_name = dataset.S3BucketName
                    try:
                        S3ShareApproval.delete_access_point_policy(
                            source_account_id,
                            target_account_id,
                            access_point_name,
                            target_env_admin,
                            prefix,
                        )
                        cleanup = S3ShareApproval.delete_access_point(source_account_id, access_point_name)
                        if cleanup:
                            S3ShareApproval.delete_target_role_access_policy(
                                target_account_id,
                                target_env_admin,
                                bucket_name,
                                access_point_name,
                                dataset,
                            )
                            S3ShareApproval.delete_dataset_bucket_key_policy(
                                source_account_id,
                                target_account_id,
                                target_env_admin,
                                dataset,
                            )
                    except Exception as e:
                        log.error(
                            f'Failed to revoke folder {prefix} '
                            f'from source account {dataset.AwsAccountId}//{dataset.region} '
                            f'with target account {target_account_id}//{target_environment.region} '
                            f'due to: {e}'
                        )
                        location = api.DatasetStorageLocation.get_location_by_s3_prefix(
                            session,
                            prefix,
                            dataset.AwsAccountId,
                            dataset.region,
                        )
                        AlarmService().trigger_revoke_folder_sharing_failure_alarm(
                            location, share, target_environment
                        )

    @staticmethod
    def manage_bucket_policy(
        dataset_admin: str,
        source_account_id: str,
        bucket_name: str,
        source_env_admin: str,
    ):
        '''
        This function will manage bucket policy by grant admin access to dataset admin, pivot role
        and environment admin. All of the policies will only be added once.
        '''
        bucket_policy = json.loads(S3.get_bucket_policy(source_account_id, bucket_name))
        for statement in bucket_policy["Statement"]:
            if statement.get("Sid") in ["AllowAllToAdmin", "DelegateAccessToAccessPoint"]:
                return
        exceptions_roleId = [f'{item}:*' for item in SessionHelper.get_role_ids(
            source_account_id,
            [dataset_admin, source_env_admin, SessionHelper.get_delegation_role_arn(source_account_id)]
        )]
        allow_owner_access = {
            "Sid": "AllowAllToAdmin",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
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
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {
                "StringEquals": {
                    "s3:DataAccessPointAccount": f"{source_account_id}"
                }
            }
        }
        bucket_policy["Statement"].append(allow_owner_access)
        bucket_policy["Statement"].append(delegated_to_accesspoint)
        S3.create_bucket_policy(source_account_id, bucket_name, json.dumps(bucket_policy))

    @staticmethod
    def grant_target_role_access_policy(
        bucket_name: str,
        access_point_name: str,
        target_account_id: str,
        target_env_admin: str,
        dataset: models.Dataset,
    ):
        existing_policy = IAM.get_role_policy(
            target_account_id,
            target_env_admin,
            "targetDatasetAccessControlPolicy",
        )
        if existing_policy:  # type dict
            if bucket_name not in ",".join(existing_policy["Statement"][0]["Resource"]):
                target_resources = [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*",
                    f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}",
                    f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}/*"
                ]
                policy = existing_policy["Statement"][0]["Resource"].extend(target_resources)
            else:
                return
        else:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:*"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*",
                            f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}",
                            f"arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{access_point_name}/*"
                        ]
                    }
                ]
            }
        IAM.update_role_policy(
            target_account_id,
            target_env_admin,
            "targetDatasetAccessControlPolicy",
            json.dumps(policy),
        )

    @staticmethod
    def manage_access_point_and_policy(
        dataset_admin: str,
        source_account_id: str,
        target_account_id: str,
        source_env_admin: str,
        target_env_admin: str,
        bucket_name: str,
        s3_prefix: str,
        access_point_name: str,
    ):
        access_point_arn = S3.get_bucket_access_point_arn(source_account_id, access_point_name)
        if not access_point_arn:
            access_point_arn = S3.create_bucket_access_point(source_account_id, bucket_name, access_point_name)
        existing_policy = S3.get_access_point_policy(source_account_id, access_point_name)
        # requester will use this role to access resources
        target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
        if existing_policy:
            # Update existing access point policy
            existing_policy = json.loads(existing_policy)
            statements = {item["Sid"]: item for item in existing_policy["Statement"]}
            if f"{target_env_admin_id}0" in statements.keys():
                prefix_list = statements[f"{target_env_admin_id}0"]["Condition"]["StringLike"]["s3:prefix"]
                if isinstance(prefix_list, str):
                    prefix_list = [prefix_list]
                if f"{s3_prefix}/*" not in prefix_list:
                    prefix_list.append(f"{s3_prefix}/*")
                    statements[f"{target_env_admin_id}0"]["Condition"]["StringLike"]["s3:prefix"] = prefix_list
                resource_list = statements[f"{target_env_admin_id}1"]["Resource"]
                if isinstance(resource_list, str):
                    resource_list = [resource_list]
                if f"{access_point_arn}/object/{s3_prefix}/*" not in resource_list:
                    resource_list.append(f"{access_point_arn}/object/{s3_prefix}/*")
                    statements[f"{target_env_admin_id}1"]["Resource"] = resource_list
                existing_policy["Statement"] = list(statements.values())
            else:
                additional_policy = S3.generate_access_point_policy_template(
                    target_env_admin_id,
                    access_point_arn,
                    s3_prefix,
                )
                existing_policy["Statement"].extend(additional_policy["Statement"])
            access_point_policy = existing_policy
        else:
            # First time to create access point policy
            access_point_policy = S3.generate_access_point_policy_template(
                target_env_admin_id,
                access_point_arn,
                s3_prefix,
            )
            exceptions_roleId = [f'{item}:*' for item in SessionHelper.get_role_ids(
                source_account_id,
                [dataset_admin, source_env_admin, SessionHelper.get_delegation_role_arn(source_account_id)]
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
        S3.attach_access_point_policy(source_account_id, access_point_name, json.dumps(access_point_policy))

    @staticmethod
    def update_dataset_bucket_key_policy(
        source_account_id: str,
        target_account_id: str,
        target_env_admin: str,
        dataset: models.Dataset,
    ):
        key_alias = f"alias/{dataset.KmsAlias}"
        kms_keyId = KMS.get_key_id(source_account_id, key_alias)
        existing_policy = KMS.get_key_policy(source_account_id, kms_keyId, "default")
        target_env_admin_id = SessionHelper.get_role_id(target_account_id, target_env_admin)
        if existing_policy and f'{target_env_admin_id}:*' not in existing_policy:
            policy = json.loads(existing_policy)
            policy["Statement"].append(
                {
                    "Sid": f"{target_env_admin_id}",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "kms:Decrypt",
                    "Resource": "*",
                    "Condition": {
                        "StringLike": {
                            "aws:userId": f"{target_env_admin_id}:*"
                        }
                    }
                }
            )
            KMS.put_key_policy(
                source_account_id,
                kms_keyId,
                "default",
                json.dumps(policy)
            )

    def handle_share_failure(
        self,
        folder: models.DatasetStorageLocation,
        share_item: models.ShareObjectItem,
        error: Exception,
    ) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Parameters
        ----------
        folder : dataset folder
        share_item : failed item
        error : share error

        Returns
        -------
        True if alarm published successfully
        """
        logging.error(
            f'Failed to share folder {folder.S3Prefix} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region}'
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            share_item,
            models.ShareObjectStatus.Share_Failed.value,
        )
        AlarmService().trigger_folder_sharing_failure_alarm(
            folder, self.share, self.target_environment
        )
        return True
