import json
import logging
from itertools import count

from dataall.base.aws.iam import IAM
from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.s3_datasets_shares.aws.kms_client import (
    KmsClient,
    DATAALL_BUCKET_KMS_DECRYPT_SID,
    DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID,
)
from dataall.modules.s3_datasets_shares.aws.s3_client import S3ControlClient, S3Client, DATAALL_READ_ONLY_SID
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.shares_base.services.share_manager_utils import ShareErrorFormatter
from dataall.modules.s3_datasets_shares.services.s3_share_alarm_service import S3ShareAlarmService
from dataall.modules.s3_datasets_shares.services.s3_share_managed_policy_service import (
    S3SharePolicyService,
    IAM_S3_BUCKETS_STATEMENT_SID,
    EMPTY_STATEMENT_SID,
)
from dataall.modules.shares_base.services.shares_enums import PrincipalType
from dataall.modules.s3_datasets.db.dataset_models import DatasetBucket
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.sharing_service import ShareData

logger = logging.getLogger(__name__)


class S3BucketShareManager:
    def __init__(
        self,
        session,
        share_data: ShareData,
        target_bucket: DatasetBucket,
    ):
        self.session = session
        self.source_env_group = share_data.source_env_group
        self.env_group = share_data.env_group
        self.dataset = share_data.dataset
        self.share = share_data.share
        self.target_bucket = target_bucket
        self.source_environment = share_data.source_environment
        self.target_environment = share_data.target_environment
        self.share_item = ShareObjectRepository.find_sharable_item(
            session,
            share_data.share.shareUri,
            target_bucket.bucketUri,
        )
        self.source_account_id = target_bucket.AwsAccountId
        self.target_account_id = share_data.target_environment.AwsAccountId
        self.source_env_admin = share_data.source_env_group.environmentIAMRoleArn
        self.target_requester_IAMRoleName = share_data.share.principalRoleName
        self.bucket_name = target_bucket.S3BucketName
        self.dataset_admin = share_data.dataset.IAMDatasetAdminRoleArn
        self.bucket_region = target_bucket.region
        self.bucket_errors = []

    def check_s3_iam_access(self) -> None:
        """
        Checks if requester IAM role policy includes requested S3 bucket and kms key permissions
        and add to bucket errors if check fails
        :return: None
        """
        logger.info(f'Check target role {self.target_requester_IAMRoleName} access policy')

        key_alias = f'alias/{self.target_bucket.KmsAlias}'
        kms_client = KmsClient(self.source_account_id, self.source_environment.region)
        kms_key_id = kms_client.get_key_id(key_alias)

        share_policy_service = S3SharePolicyService(
            environmentUri=self.target_environment.environmentUri,
            account=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            role_name=self.target_requester_IAMRoleName,
            resource_prefix=self.target_environment.resourcePrefix,
        )
        share_resource_policy_name = share_policy_service.generate_policy_name()

        if not share_policy_service.check_if_policy_exists():
            logger.info(f'IAM Policy {share_resource_policy_name} does not exist')
            self.bucket_errors.append(ShareErrorFormatter.dne_error_msg('IAM Policy', share_resource_policy_name))
            return

        if not share_policy_service.check_if_policy_attached():
            logger.info(
                f'IAM Policy {share_resource_policy_name} exists but is not attached to role {self.share.principalRoleName}'
            )
            self.bucket_errors.append(
                ShareErrorFormatter.dne_error_msg('IAM Policy attached', share_resource_policy_name)
            )
            return

        s3_target_resources = [f'arn:aws:s3:::{self.bucket_name}', f'arn:aws:s3:::{self.bucket_name}/*']

        version_id, policy_document = IAM.get_managed_policy_default_version(
            self.target_environment.AwsAccountId, self.target_environment.region, share_resource_policy_name
        )
        s3_statement_index = S3SharePolicyService._get_statement_by_sid(
            policy_document, f'{IAM_S3_BUCKETS_STATEMENT_SID}S3'
        )

        if s3_statement_index is None:
            logger.info(f'IAM Policy Statement {IAM_S3_BUCKETS_STATEMENT_SID}S3 does not exist')
            self.bucket_errors.append(
                ShareErrorFormatter.missing_permission_error_msg(
                    self.target_requester_IAMRoleName,
                    'IAM Policy Statement',
                    f'{IAM_S3_BUCKETS_STATEMENT_SID}S3',
                    'S3 Bucket',
                    f'{self.bucket_name}',
                )
            )
        elif not share_policy_service.check_resource_in_policy_statement(
            target_resources=s3_target_resources,
            existing_policy_statement=policy_document['Statement'][s3_statement_index],
        ):
            logger.info(
                f'IAM Policy Statement {IAM_S3_BUCKETS_STATEMENT_SID}S3 does not contain resources {s3_target_resources}'
            )
            self.bucket_errors.append(
                ShareErrorFormatter.missing_permission_error_msg(
                    self.target_requester_IAMRoleName,
                    'IAM Policy Resource',
                    f'{IAM_S3_BUCKETS_STATEMENT_SID}S3',
                    'S3 Bucket',
                    f'{self.bucket_name}',
                )
            )
        else:
            policy_check, missing_permissions, extra_permissions = (
                share_policy_service.check_s3_actions_in_policy_statement(
                    existing_policy_statement=policy_document['Statement'][s3_statement_index]
                )
            )
            if not policy_check:
                logger.info(f'IAM Policy Statement {IAM_S3_BUCKETS_STATEMENT_SID}S3 has invalid actions')
                if missing_permissions:
                    self.bucket_errors.append(
                        ShareErrorFormatter.missing_permission_error_msg(
                            self.target_requester_IAMRoleName,
                            'IAM Policy Action',
                            missing_permissions,
                            'S3 Bucket',
                            f'{self.bucket_name}',
                        )
                    )
                if extra_permissions:
                    self.bucket_errors.append(
                        ShareErrorFormatter.not_allowed_permission_error_msg(
                            self.target_requester_IAMRoleName,
                            'IAM Policy Action',
                            extra_permissions,
                            'S3 Bucket',
                            f'{self.bucket_name}',
                        )
                    )

        if kms_key_id:
            kms_statement_index = S3SharePolicyService._get_statement_by_sid(
                policy_document, f'{IAM_S3_BUCKETS_STATEMENT_SID}KMS'
            )
            kms_target_resources = [f'arn:aws:kms:{self.bucket_region}:{self.source_account_id}:key/{kms_key_id}']
            if kms_statement_index is None:
                logger.info(f'IAM Policy Statement {IAM_S3_BUCKETS_STATEMENT_SID}KMS does not exist')
                self.bucket_errors.append(
                    ShareErrorFormatter.missing_permission_error_msg(
                        self.target_requester_IAMRoleName,
                        'IAM Policy Statement',
                        f'{IAM_S3_BUCKETS_STATEMENT_SID}KMS',
                        'KMS Key',
                        f'{kms_key_id}',
                    )
                )

            elif not share_policy_service.check_resource_in_policy_statement(
                target_resources=kms_target_resources,
                existing_policy_statement=policy_document['Statement'][kms_statement_index],
            ):
                logger.info(
                    f'IAM Policy Statement {IAM_S3_BUCKETS_STATEMENT_SID}KMS does not contain resources {kms_target_resources}'
                )
                self.bucket_errors.append(
                    ShareErrorFormatter.missing_permission_error_msg(
                        self.target_requester_IAMRoleName,
                        'IAM Policy Resource',
                        f'{IAM_S3_BUCKETS_STATEMENT_SID}KMS',
                        'KMS Key',
                        f'{kms_key_id}',
                    )
                )
        return

    def grant_s3_iam_access(self):
        """
        Updates requester IAM role policy to include requested S3 bucket and kms key
        :return:
        """
        logger.info(f'Grant target role {self.target_requester_IAMRoleName} access policy')

        share_policy_service = S3SharePolicyService(
            environmentUri=self.target_environment.environmentUri,
            account=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            role_name=self.target_requester_IAMRoleName,
            resource_prefix=self.target_environment.resourcePrefix,
        )

        # Backwards compatibility
        # we check if a managed share policy exists. If False, the role was introduced to data.all before this update
        # We create the policy from the inline statements and attach it to the role
        if not share_policy_service.check_if_policy_exists():
            share_policy_service.create_managed_policy_from_inline_and_delete_inline()
            share_policy_service.attach_policy()
        # End of backwards compatibility

        if not share_policy_service.check_if_policy_attached():
            if self.share.principalType == PrincipalType.Group.value:
                share_policy_service.attach_policy()
            else:
                consumption_role = EnvironmentService.get_consumption_role(
                    session=self.session, uri=self.share.principalId
                )
                if consumption_role.dataallManaged:
                    share_policy_service.attach_policy()

        share_resource_policy_name = share_policy_service.generate_policy_name()

        logger.info(f'Share policy name is {share_resource_policy_name}')
        version_id, policy_document = IAM.get_managed_policy_default_version(
            self.target_account_id, self.target_environment.region, share_resource_policy_name
        )

        key_alias = f'alias/{self.target_bucket.KmsAlias}'
        kms_client = KmsClient(self.source_account_id, self.source_environment.region)
        kms_key_id = kms_client.get_key_id(key_alias)

        s3_target_resources = [f'arn:aws:s3:::{self.bucket_name}', f'arn:aws:s3:::{self.bucket_name}/*']

        share_policy_service.add_missing_resources_to_policy_statement(
            resource_type='s3',
            target_resources=s3_target_resources,
            statement_sid=f'{IAM_S3_BUCKETS_STATEMENT_SID}S3',
            policy_document=policy_document,
        )

        share_policy_service.remove_empty_statement(policy_doc=policy_document, statement_sid=EMPTY_STATEMENT_SID)

        if kms_key_id:
            kms_target_resources = [f'arn:aws:kms:{self.bucket_region}:{self.source_account_id}:key/{kms_key_id}']
            share_policy_service.add_missing_resources_to_policy_statement(
                resource_type='kms',
                target_resources=kms_target_resources,
                statement_sid=f'{IAM_S3_BUCKETS_STATEMENT_SID}KMS',
                policy_document=policy_document,
            )

        IAM.update_managed_policy_default_version(
            self.target_account_id,
            self.target_environment.region,
            share_resource_policy_name,
            version_id,
            json.dumps(policy_document),
        )

    def get_bucket_policy_or_default(self):
        """
        Fetches the existing bucket policy for the S3 bucket if one exists otherwise returns the default bucket policy
        :return:
        """
        s3_client = S3Client(self.source_account_id, self.source_environment.region)
        bucket_policy = s3_client.get_bucket_policy(self.bucket_name)
        if bucket_policy:
            logger.info(
                f'There is already an existing policy for bucket {self.bucket_name}, will be updating policy...'
            )
            bucket_policy = json.loads(bucket_policy)
        else:
            logger.info(f'Bucket policy for {self.bucket_name} does not exist, generating default policy...')
            bucket_policy = S3ControlClient.generate_default_bucket_policy(self.bucket_name)
        return bucket_policy

    def check_role_bucket_policy(self) -> None:
        """
        This function checks if the bucket policy grants read only access to accepted share roles
        and add to bucket errors if check fails
        :return: None
        """
        target_requester_arn = IAM.get_role_arn_by_name(
            self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
        )
        if not target_requester_arn:
            self.bucket_errors.append(f'Principal role {self.target_requester_IAMRoleName} is not found.')
            return
        s3_client = S3Client(self.source_account_id, self.source_environment.region)
        bucket_policy = s3_client.get_bucket_policy(self.bucket_name)
        error = False
        if not bucket_policy:
            error = True
        else:
            bucket_policy = json.loads(bucket_policy)
            counter = count()
            statements = {item.get('Sid', next(counter)): item for item in bucket_policy.get('Statement', {})}
            if DATAALL_READ_ONLY_SID not in statements.keys():
                error = True
            elif f'{target_requester_arn}' not in self.get_principal_list(statements[DATAALL_READ_ONLY_SID]):
                error = True
        if error:
            self.bucket_errors.append(
                ShareErrorFormatter.missing_permission_error_msg(
                    target_requester_arn, 'Bucket Policy', DATAALL_READ_ONLY_SID, 'S3 Bucket', f'{self.bucket_name}'
                )
            )

    def grant_role_bucket_policy(self):
        """
        This function will update bucket policy by granting admin access to dataset admin, pivot role
        and environment admin along with read only access to accepted share roles. All the policies will only be added
        once.
        :return:
        """
        logger.info(f'Granting access via Bucket policy for {self.bucket_name}')
        try:
            target_requester_arn = IAM.get_role_arn_by_name(
                self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
            )
            if not target_requester_arn:
                raise PrincipalRoleNotFound(
                    'grant role bucket policy', f'Principal role {self.target_requester_IAMRoleName} is not found.'
                )
            bucket_policy = self.get_bucket_policy_or_default()
            counter = count()
            statements = {item.get('Sid', next(counter)): item for item in bucket_policy.get('Statement', {})}
            if DATAALL_READ_ONLY_SID in statements.keys():
                logger.info(f'Bucket policy contains share statement {DATAALL_READ_ONLY_SID}, updating the current one')
                statements[DATAALL_READ_ONLY_SID] = self.add_target_arn_to_statement_principal(
                    statements[DATAALL_READ_ONLY_SID], target_requester_arn
                )
            else:
                logger.info(
                    f'Bucket policy does not contain share statement {DATAALL_READ_ONLY_SID}, generating a new one'
                )
                statements[DATAALL_READ_ONLY_SID] = self.generate_default_bucket_read_policy_statement(
                    self.bucket_name, target_requester_arn
                )

            bucket_policy['Statement'] = list(statements.values())
            s3_client = S3Client(self.source_account_id, self.source_environment.region)
            s3_client.create_bucket_policy(self.bucket_name, json.dumps(bucket_policy))
        except Exception as e:
            logger.exception(f'Failed during bucket policy management {e}')
            raise e

    def add_target_arn_to_statement_principal(self, statement, target_requester_arn):
        principal_list = self.get_principal_list(statement)
        if f'{target_requester_arn}' not in principal_list:
            principal_list.append(f'{target_requester_arn}')
        statement['Principal']['AWS'] = principal_list
        return statement

    @staticmethod
    def get_principal_list(statement):
        principal_list = statement['Principal']['AWS']
        if isinstance(principal_list, str):
            principal_list = [principal_list]
        return principal_list

    def check_dataset_bucket_key_policy(self) -> None:
        """
        Checks if dataset kms key policy includes read permissions for requestors IAM Role
        and add to bucket errors if check fails
        :return: None
        """
        key_alias = f'alias/{self.target_bucket.KmsAlias}'
        kms_client = KmsClient(self.source_account_id, self.source_environment.region)
        kms_key_id = kms_client.get_key_id(key_alias)
        existing_policy = kms_client.get_key_policy(kms_key_id)

        if not existing_policy:
            self.bucket_errors.append(ShareErrorFormatter.dne_error_msg('KMS Key Policy', kms_key_id))
            return

        target_requester_arn = IAM.get_role_arn_by_name(
            self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
        )
        if not target_requester_arn:
            self.bucket_errors.append(f'Principal role {self.target_requester_IAMRoleName} is not found.')
            return

        existing_policy = json.loads(existing_policy)
        counter = count()
        statements = {item.get('Sid', next(counter)): item for item in existing_policy.get('Statement', {})}

        error = False
        if DATAALL_BUCKET_KMS_DECRYPT_SID not in statements.keys():
            error = True
        elif f'{target_requester_arn}' not in self.get_principal_list(statements[DATAALL_BUCKET_KMS_DECRYPT_SID]):
            error = True
        if error:
            self.bucket_errors.append(
                ShareErrorFormatter.missing_permission_error_msg(
                    self.target_requester_IAMRoleName,
                    'KMS Key Policy',
                    DATAALL_BUCKET_KMS_DECRYPT_SID,
                    'KMS Key',
                    f'{kms_key_id}',
                )
            )
        return

    def grant_dataset_bucket_key_policy(self):
        if (self.target_bucket.imported and self.target_bucket.importedKmsKey) or not self.target_bucket.imported:
            logger.info('Updating dataset Bucket KMS key policy...')
            key_alias = f'alias/{self.target_bucket.KmsAlias}'
            kms_client = KmsClient(self.source_account_id, self.source_environment.region)
            kms_key_id = kms_client.get_key_id(key_alias)
            existing_policy = kms_client.get_key_policy(kms_key_id)
            target_requester_arn = IAM.get_role_arn_by_name(
                self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
            )
            if not target_requester_arn:
                raise PrincipalRoleNotFound(
                    'grant dataset bucket key policy',
                    f'Principal role {self.target_requester_IAMRoleName} is not found. Fail to update KMS policy',
                )

            pivot_role_name = SessionHelper.get_delegation_role_name(self.source_environment.region)

            if existing_policy:
                existing_policy = json.loads(existing_policy)
                counter = count()
                statements = {item.get('Sid', next(counter)): item for item in existing_policy.get('Statement', {})}

                if DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID in statements.keys():
                    logger.info(
                        f'KMS key policy already contains share statement {DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}, updating existing statement'
                    )

                else:
                    logger.info(
                        f'KMS key policy does not contain statement {DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}, generating a new one'
                    )
                statements[DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID] = (
                    self.generate_enable_pivot_role_permissions_policy_statement(
                        pivot_role_name, self.source_account_id
                    )
                )

                if DATAALL_BUCKET_KMS_DECRYPT_SID in statements.keys():
                    logger.info(
                        f'KMS key policy contains share statement {DATAALL_BUCKET_KMS_DECRYPT_SID}, updating the current one'
                    )
                    statements[DATAALL_BUCKET_KMS_DECRYPT_SID] = self.add_target_arn_to_statement_principal(
                        statements[DATAALL_BUCKET_KMS_DECRYPT_SID], target_requester_arn
                    )
                else:
                    logger.info(
                        f'KMS key does not contain share statement {DATAALL_BUCKET_KMS_DECRYPT_SID}, generating a new one'
                    )
                    statements[DATAALL_BUCKET_KMS_DECRYPT_SID] = self.generate_default_kms_decrypt_policy_statement(
                        target_requester_arn
                    )
                existing_policy['Statement'] = list(statements.values())

            else:
                logger.info('KMS key policy does not contain any statements, generating a new one')
                existing_policy = {
                    'Version': '2012-10-17',
                    'Statement': [
                        self.generate_default_kms_decrypt_policy_statement(target_requester_arn),
                        self.generate_enable_pivot_role_permissions_policy_statement(
                            pivot_role_name, self.source_account_id
                        ),
                    ],
                }
            kms_client.put_key_policy(kms_key_id, json.dumps(existing_policy))

    def delete_target_role_bucket_policy(self):
        logger.info(f'Deleting target role from bucket policy for bucket {self.bucket_name}...')
        try:
            s3_client = S3Client(self.source_account_id, self.source_environment.region)
            bucket_policy = json.loads(s3_client.get_bucket_policy(self.bucket_name))
            target_requester_arn = IAM.get_role_arn_by_name(
                self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
            )
            if not target_requester_arn:
                # if somehow the role was deleted, we can only try to guess the role arn (quite easy, though)
                target_requester_arn = f'arn:aws:iam::{self.target_account_id}:role/{self.target_requester_IAMRoleName}'
            counter = count()
            statements = {item.get('Sid', next(counter)): item for item in bucket_policy.get('Statement', {})}
            if DATAALL_READ_ONLY_SID in statements.keys():
                principal_list = self.get_principal_list(statements[DATAALL_READ_ONLY_SID])
                if f'{target_requester_arn}' in principal_list:
                    principal_list.remove(f'{target_requester_arn}')
                    if len(principal_list) == 0:
                        statements.pop(DATAALL_READ_ONLY_SID)
                    else:
                        statements[DATAALL_READ_ONLY_SID]['Principal']['AWS'] = principal_list
                    bucket_policy['Statement'] = list(statements.values())
                    s3_client.create_bucket_policy(self.bucket_name, json.dumps(bucket_policy))
        except Exception as e:
            logger.exception(f'Failed during bucket policy management {e}')
            raise e

    def delete_target_role_access_policy(
        self,
        share: ShareObject,
        target_bucket: DatasetBucket,
        target_environment: Environment,
    ):
        logger.info('Deleting target role IAM statements...')

        share_policy_service = S3SharePolicyService(
            role_name=share.principalRoleName,
            account=target_environment.AwsAccountId,
            region=self.target_environment.region,
            environmentUri=target_environment.environmentUri,
            resource_prefix=target_environment.resourcePrefix,
        )
        # Backwards compatibility
        # we check if a managed share policy exists. If False, the role was introduced to data.all before this update
        # We create the policy from the inline statements and attach it to the role
        if not share_policy_service.check_if_policy_exists():
            share_policy_service.create_managed_policy_from_inline_and_delete_inline()
            share_policy_service.attach_policy()
        # End of backwards compatibility

        share_resource_policy_name = share_policy_service.generate_policy_name()
        version_id, policy_document = IAM.get_managed_policy_default_version(
            self.target_account_id, self.target_environment.region, share_resource_policy_name
        )

        key_alias = f'alias/{target_bucket.KmsAlias}'
        kms_client = KmsClient(target_bucket.AwsAccountId, target_bucket.region)
        kms_key_id = kms_client.get_key_id(key_alias)

        s3_target_resources = [
            f'arn:aws:s3:::{target_bucket.S3BucketName}',
            f'arn:aws:s3:::{target_bucket.S3BucketName}/*',
        ]
        share_policy_service.remove_resource_from_statement(
            target_resources=s3_target_resources,
            statement_sid=f'{IAM_S3_BUCKETS_STATEMENT_SID}S3',
            policy_document=policy_document,
        )
        if kms_key_id:
            kms_target_resources = [f'arn:aws:kms:{target_bucket.region}:{target_bucket.AwsAccountId}:key/{kms_key_id}']
            share_policy_service.remove_resource_from_statement(
                target_resources=kms_target_resources,
                statement_sid=f'{IAM_S3_BUCKETS_STATEMENT_SID}KMS',
                policy_document=policy_document,
            )

        IAM.update_managed_policy_default_version(
            self.target_account_id,
            self.target_environment.region,
            share_resource_policy_name,
            version_id,
            json.dumps(policy_document),
        )

    def delete_target_role_bucket_key_policy(
        self,
        target_bucket: DatasetBucket,
    ):
        if (target_bucket.imported and target_bucket.importedKmsKey) or not target_bucket.imported:
            logger.info('Deleting target role from dataset bucket KMS key policy...')
            key_alias = f'alias/{target_bucket.KmsAlias}'
            kms_client = KmsClient(target_bucket.AwsAccountId, target_bucket.region)
            kms_key_id = kms_client.get_key_id(key_alias)
            existing_policy = json.loads(kms_client.get_key_policy(kms_key_id))
            target_requester_arn = IAM.get_role_arn_by_name(
                self.target_account_id, self.target_environment.region, self.target_requester_IAMRoleName
            )
            if target_requester_arn is None:
                target_requester_arn = f'arn:aws:iam::{self.target_account_id}:role/{self.target_requester_IAMRoleName}'
            counter = count()
            statements = {item.get('Sid', next(counter)): item for item in existing_policy.get('Statement', {})}
            if DATAALL_BUCKET_KMS_DECRYPT_SID in statements.keys():
                principal_list = self.get_principal_list(statements[DATAALL_BUCKET_KMS_DECRYPT_SID])
                if f'{target_requester_arn}' in principal_list:
                    principal_list.remove(f'{target_requester_arn}')
                    if len(principal_list) == 0:
                        statements.pop(DATAALL_BUCKET_KMS_DECRYPT_SID)
                    else:
                        statements[DATAALL_BUCKET_KMS_DECRYPT_SID]['Principal']['AWS'] = principal_list
                    existing_policy['Statement'] = list(statements.values())
                    kms_client.put_key_policy(kms_key_id, json.dumps(existing_policy))

    def handle_share_failure(self, error: Exception) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Returns
        -------
        True if alarm published successfully
        """
        logger.error(
            f'Failed to share bucket {self.target_bucket.S3BucketName} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        S3ShareAlarmService().trigger_s3_bucket_sharing_failure_alarm(
            self.target_bucket, self.share, self.target_environment
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
            f'Failed to revoke S3 permissions to bucket {self.bucket_name} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        S3ShareAlarmService().trigger_revoke_s3_bucket_sharing_failure_alarm(
            self.target_bucket, self.share, self.target_environment
        )
        return True

    @staticmethod
    def generate_default_bucket_read_policy_statement(s3_bucket_name, target_requester_arn):
        return {
            'Sid': f'{DATAALL_READ_ONLY_SID}',
            'Effect': 'Allow',
            'Principal': {'AWS': [f'{target_requester_arn}']},
            'Action': ['s3:List*', 's3:GetObject'],
            'Resource': [f'arn:aws:s3:::{s3_bucket_name}', f'arn:aws:s3:::{s3_bucket_name}/*'],
        }

    @staticmethod
    def generate_default_kms_decrypt_policy_statement(target_requester_arn):
        return {
            'Sid': f'{DATAALL_BUCKET_KMS_DECRYPT_SID}',
            'Effect': 'Allow',
            'Principal': {'AWS': [f'{target_requester_arn}']},
            'Action': 'kms:Decrypt',
            'Resource': '*',
        }

    @staticmethod
    def generate_enable_pivot_role_permissions_policy_statement(pivot_role_name, source_account_id):
        return {
            'Sid': f'{DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID}',
            'Effect': 'Allow',
            'Principal': {'AWS': [f'arn:aws:iam::{source_account_id}:role/{pivot_role_name}']},
            'Action': [
                'kms:Decrypt',
                'kms:Encrypt',
                'kms:GenerateDataKey*',
                'kms:PutKeyPolicy',
                'kms:GetKeyPolicy',
                'kms:ReEncrypt*',
                'kms:TagResource',
                'kms:UntagResource',
                'kms:DescribeKey',
                'kms:List*',
            ],
            'Resource': '*',
        }
