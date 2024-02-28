import json
from dataall.base.aws.iam import IAM
from dataall.base.utils.naming_convention import NamingConventionService, NamingConventionPattern
from dataall.core.environment.services.managed_iam_policies import ManagedPolicy
import logging

log = logging.getLogger(__name__)

OLD_IAM_ACCESS_POINT_ROLE_POLICY = "targetDatasetAccessControlPolicy"
OLD_IAM_S3BUCKET_ROLE_POLICY = "dataall-targetDatasetS3Bucket-AccessControlPolicy"
FAKE_S3_PLACEHOLDER = "arn:aws:s3:::initial-fake-empty-bucket"

IAM_S3_ACCESS_POINTS_STATEMENT_SID = "AccessPointsStatement"
IAM_S3_BUCKETS_STATEMENT_SID = "BucketStatement"


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
                    "Sid": f"{IAM_S3_ACCESS_POINTS_STATEMENT_SID}S3",
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": [
                        FAKE_S3_PLACEHOLDER,
                    ]
                },
                {
                    "Sid": f"{IAM_S3_BUCKETS_STATEMENT_SID}S3",
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

    @staticmethod
    def remove_empty_fake_resource(policy_doc, statement_sid):
        # TODO remove this fake resource in a more elegant way
        statement_index = SharePolicyService._get_statement_by_sid(policy_doc, statement_sid)
        if FAKE_S3_PLACEHOLDER in policy_doc["Statement"][statement_index]["Resource"]:
            policy_doc["Statement"][statement_index]["Resource"].remove(FAKE_S3_PLACEHOLDER)
        return policy_doc

    def add_missing_resources_to_policy_statement(
            self,
            resource_type,
            target_resources,
            statement_sid,
            policy_document
    ):
        """
        Checks if the resources are in the existing statement. Otherwise, it will add it.
        :param target_resources: list
        :param existing_policy_statement: dict
        :return
        """
        policy_name = self.generate_policy_name()
        index = self._get_statement_by_sid(policy_document, statement_sid)
        if index is None:
            log.info(
                f'{statement_sid} does NOT exists for Managed policy {policy_name} '
                f'creating statement...'
            )
            additional_policy = {
                "Sid": statement_sid,
                "Effect": "Allow",
                "Action": [
                    f"{resource_type}:*"
                ],
                "Resource": target_resources
            }
            policy_document["Statement"].append(additional_policy)
        else:
            for target_resource in target_resources:
                if target_resource not in policy_document["Statement"][index]["Resource"]:
                    log.info(
                        f'{statement_sid} exists for Managed policy {policy_name} '
                        f'but {target_resource} is not included, updating...'
                    )
                    policy_document["Statement"][index]["Resource"].extend([target_resource])
                else:
                    log.info(
                        f'{statement_sid} exists for Managed policy {policy_name} '
                        f'and {target_resource} is included, skipping...'
                    )

    def remove_resource_from_statement(self, resource_type, target_resources, statement_sid, policy_document):
        policy_name = self.generate_policy_name()
        index = self._get_statement_by_sid(policy_document, statement_sid)
        log.info(
            f'Removing {target_resources} from Statement[{index}] in Managed policy {policy_name} '
            f'skipping...'
        )
        if index is None:
            log.info(
                f'{statement_sid} does NOT exists for Managed policy {policy_name} '
                f'skipping...'
            )
        else:
            policy_statement = policy_document["Statement"][index]
            for target_resource in target_resources:
                if target_resource in policy_statement["Resource"]:
                    log.info(
                        f'{statement_sid} exists for Managed policy {policy_name} '
                        f'and {target_resource} is included, removing...'
                    )
                    policy_statement["Resource"].remove(target_resource)
                if len(policy_statement["Resource"]) == 0:
                    if resource_type == "s3":
                        log.info(
                            f'No more resources in {statement_sid}, appending {FAKE_S3_PLACEHOLDER}...'
                        )
                        policy_statement["Resource"].append(FAKE_S3_PLACEHOLDER)
                    if resource_type == "kms":
                        log.info(
                            f'No more resources in {statement_sid}, removing statement...'
                        )
                        policy_document["Statement"].pop(index)

    @staticmethod
    def _get_statement_by_sid(policy, sid):
        for index, statement in enumerate(policy["Statement"]):
            if statement["Sid"] == sid:
                return index
        return None

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
        existing_bucket_s3, existing_bucket_kms = self._get_policy_resources_from_inline_policy(OLD_IAM_S3BUCKET_ROLE_POLICY)
        existing_access_points_s3, existing_access_points_kms = self._get_policy_resources_from_inline_policy(OLD_IAM_S3BUCKET_ROLE_POLICY)

        updated_policy = self._update_policy_resources_from_inline_policy(
            policy=new_policy,
            statement_sid=IAM_S3_BUCKETS_STATEMENT_SID,
            existing_s3=existing_bucket_s3,
            existing_kms=existing_bucket_kms
        )
        updated_policy = self._update_policy_resources_from_inline_policy(
            policy=updated_policy,
            statement_sid=IAM_S3_ACCESS_POINTS_STATEMENT_SID,
            existing_s3=existing_access_points_s3,
            existing_kms=existing_access_points_kms
        )
        return updated_policy

    def _get_policy_resources_from_inline_policy(self, policy_name):
        # This function can only be used for backwards compatibility where policies had statement[0] for s3
        # and statement[1] for KMS permissions
        try:
            existing_policy = IAM.get_role_policy(
                self.account,
                self.role_name,
                policy_name
            )
            if existing_policy is not None:
                kms_resources = existing_policy["Statement"][1]["Resource"] if len(existing_policy["Statement"]) > 1 else []
                return existing_policy["Statement"][0]["Resource"], kms_resources
            else:
                return [], []
        except Exception as e:
            log.error(
                f'Failed to retrieve the existing policy {policy_name}: {e} '
            )
            return [], []

    def _update_policy_resources_from_inline_policy(self, policy, statement_sid, existing_s3, existing_kms):
        # This function can only be used for backwards compatibility where policies had statement[0] for s3
        # and statement[1] for KMS permissions
        if len(existing_s3) > 0:
            s3_index = self._get_statement_by_sid(policy, f"{statement_sid}-S3")
            policy["Statement"][s3_index]["Resource"] = existing_s3
            SharePolicyService.remove_empty_fake_resource(policy, s3_index)
        if len(existing_kms) > 0:
            additional_policy = {
                "Sid": f"{statement_sid}KMS",
                "Effect": "Allow",
                "Action": [
                    "kms:*"
                ],
                "Resource": existing_kms
            }
            policy["Statement"].append(additional_policy)
        return policy
