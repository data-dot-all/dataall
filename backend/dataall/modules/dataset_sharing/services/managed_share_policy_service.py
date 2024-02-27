import json
from dataall.base.aws.iam import IAM
from dataall.base.utils.naming_convention import NamingConventionService, NamingConventionPattern
from dataall.core.environment.services.managed_iam_policies import ManagedPolicy
import logging

log = logging.getLogger(__name__)

OLD_IAM_ACCESS_POINT_ROLE_POLICY = "targetDatasetAccessControlPolicy"
OLD_IAM_S3BUCKET_ROLE_POLICY = "dataall-targetDatasetS3Bucket-AccessControlPolicy"
FAKE_S3_PLACEHOLDER = "arn:aws:s3:::initial-fake-empty-bucket"


class SharePolicyService(ManagedPolicy):
    def __init__(
            self,
            role_name,
            account,
            environmentUri,
            resource_prefix
    ):
        self.role_name = role_name
        self.account = account
        self.environmentUri = environmentUri
        self.resource_prefix = resource_prefix

    @property
    def policy_type(self):
        return "SharePolicy"

    def generate_policy_name(self) -> str:
        # In this case it is not possible to build a too long policy because the IAM role can be max 64 chars
        # However it is good practice to use the standard utility to build the name
        return NamingConventionService(
            target_label=f'env-{self.environmentUri}-share-policy',
            target_uri=self.role_name,
            pattern=NamingConventionPattern.IAM_POLICY,
            resource_prefix=self.resource_prefix
        ).build_compliant_name()

    def generate_empty_policy(self) -> dict:
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": [
                        FAKE_S3_PLACEHOLDER,
                    ]
                }
            ]
        }

    def check_if_policy_exists(self) -> bool:
        policy_name = self.generate_policy_name()
        share_policy = IAM.get_policy_by_name(self.account, policy_name)
        return (share_policy is not None)

    def check_if_policy_attached(self):
        policy_name = self.generate_policy_name()
        return IAM.is_policy_attached(self.account, policy_name, self.role_name)

    def attach_policy(self):
        policy_arn = f"arn:aws:iam::{self.account}:policy/{self.generate_policy_name()}"
        try:
            log.info(f'Attaching policy {policy_arn}')
            IAM.attach_role_policy(
                self.account,
                self.role_name,
                policy_arn
            )
        except Exception as e:
            raise Exception(
                f"Required customer managed policy {policy_arn} can't be attached: {e}")

    @staticmethod
    def remove_empty_fake_resource(policy_doc):
        # TODO remove this fake resource in a more elegant way
        if FAKE_S3_PLACEHOLDER in policy_doc["Statement"][0]["Resource"]:
            policy_doc["Statement"][0]["Resource"].remove(FAKE_S3_PLACEHOLDER)
        return policy_doc

    # Backwards compatibility

    def create_managed_policy_from_inline_and_delete_inline(self):
        """
        For existing consumption and team roles, the IAM managed policy won't be created.
        We need to create the policy based on the inline statements
        Finally, delete the old obsolete inline policies from the role
        """
        try:
            policy_document = self._generate_managed_policy_from_inline_policies()
            log.info(f'Creating policy from inline backwards compatibility. Policy = {str(policy_document)}')
            policy_arn = IAM.create_managed_policy(self.account, self.generate_policy_name(),
                                                   json.dumps(policy_document))

            # Delete obsolete inline policies
            log.info(f'Deleting {OLD_IAM_ACCESS_POINT_ROLE_POLICY} and {OLD_IAM_S3BUCKET_ROLE_POLICY}')
            IAM.delete_role_policy(self.account, self.role_name, OLD_IAM_ACCESS_POINT_ROLE_POLICY)
            IAM.delete_role_policy(self.account, self.role_name, OLD_IAM_S3BUCKET_ROLE_POLICY)

        except Exception as e:
            raise Exception(f"Error creating policy from inline policies: {e}")
        return policy_arn

    def _generate_managed_policy_from_inline_policies(self):
        """
        Get resources shared in previous inline policies
        If there are already shared resources, add them to the empty policy and remove the fake statement
        return: IAM policy document
        """
        new_policy = self.generate_empty_policy()
        existing_bucket_s3, existing_bucket_kms = self._get_policy_resources(OLD_IAM_S3BUCKET_ROLE_POLICY)
        existing_access_points_s3, existing_access_points_kms = self._get_policy_resources(OLD_IAM_S3BUCKET_ROLE_POLICY)
        s3_resources = existing_bucket_s3.extend(existing_access_points_s3)
        kms_resources = existing_bucket_kms.extend(existing_access_points_kms)
        if len(s3_resources) > 0:
            new_policy["Statement"][0]["Resource"] = s3_resources
            SharePolicyService.remove_empty_fake_resource(new_policy)
        if len(kms_resources) > 0:
            additional_policy = {
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": kms_resources
            }
            new_policy["Statement"].append(additional_policy)
        return new_policy

    def _get_policy_resources(self, policy_name):
        try:
            existing_policy = IAM.get_role_policy(
                self.account,
                self.role_name,
                policy_name
            )
            kms_resources = existing_policy["Statement"][1]["Resource"] if len(existing_policy["Statement"]) > 1 else []
            return existing_policy["Statement"][0]["Resource"], kms_resources
        except Exception as e:
            log.error(
                f'Failed to retrieve the existing policy {policy_name}: {e} '
            )
            return [], []
