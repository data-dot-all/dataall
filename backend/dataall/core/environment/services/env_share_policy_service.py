import json
from dataall.base.aws.iam import IAM
import logging

log = logging.getLogger(__name__)

IAM_ACCESS_POINT_ROLE_POLICY = "targetDatasetAccessControlPolicy"
IAM_S3BUCKET_ROLE_POLICY = "dataall-targetDatasetS3Bucket-AccessControlPolicy"


class SharePolicyService:

    @staticmethod
    def generate_share_policy_name(environment_uri, iam_role_name):
        return f'dataall-env-{environment_uri}-share-{iam_role_name}'

    @staticmethod
    # returns share policy name and a flag, if it's attached or not
    def get_share_policy_status(iam_role_name, environmentUri, AWSAccountId) -> (str, bool):

        policy_name = SharePolicyService.generate_share_policy_name(environmentUri, iam_role_name)

        return policy_name, IAM.is_policy_attached(AWSAccountId, policy_name, iam_role_name)

    @staticmethod
    def check_if_share_policy_exists(iam_role_name, environmentUri, AWSAccountId):
        policy_name = SharePolicyService.generate_share_policy_name(environmentUri, iam_role_name)
        share_policy = IAM.get_policy_by_name(AWSAccountId, policy_name)
        return (share_policy is not None)

    @staticmethod
    def create_and_attach_share_policy_for_existing_role(iam_role_name, environmentUri, AWSAccountId):
        share_policy_name = SharePolicyService.generate_share_policy_name(environmentUri, iam_role_name)
        try:
            policy_document = SharePolicyService.empty_share_policy_document()
            # if there were inline policies with already shared resources,
            # let's add these resources to new managed policy
            SharePolicyService.fill_policy_with_existing_resources(AWSAccountId, iam_role_name, policy_document)
            log.info(f"Required share policy does not exist. Let's create one with name: {share_policy_name}")
            share_policy_arn = IAM.create_managed_policy(AWSAccountId, share_policy_name,
                                                         json.dumps(policy_document))
            SharePolicyService.delete_obsolete_inline_policies(AWSAccountId, iam_role_name)
            try:
                log.info('Let`s attach missing policies')
                IAM.attach_role_policy(
                    AWSAccountId,
                    iam_role_name,
                    share_policy_arn
                )
            except Exception as e:
                raise Exception(f"Required customer managed policy {share_policy_name} can't be attached: {e}")
        except Exception as e:
            raise Exception(
                f"Required customer managed policy {share_policy_name} does not exist and failed to be created: {e}")

    @staticmethod
    def ensure_share_policy_attached(iam_role_name,
                                     dataallManaged,
                                     environmentUri,
                                     AWSAccountId,
                                     attachMissingPolicies: bool
                                     ):

        share_policy_name, is_share_policy_attached = SharePolicyService.get_share_policy_status(iam_role_name,
                                                                                                 environmentUri,
                                                                                                 AWSAccountId)
        # if the policy already attached -- fine, nothing else to do here
        if is_share_policy_attached:
            return

            # if policy is not attached and the role is
        # a) customer managed
        # b) user don't want us to attach policy
        # we raise an Exception
        if not (dataallManaged or attachMissingPolicies):
            raise Exception(
                f"Required customer managed policy {share_policy_name} is not attached to role {iam_role_name}")

        # For the roles, that existed before this update, there are no managed share policy.
        # We need to create one and transfer all existed shared resources there
        # let's check, that the policy exists and if not, create it
        share_policy = IAM.get_policy_by_name(AWSAccountId, share_policy_name)
        if share_policy is None:
            SharePolicyService.create_and_attach_share_policy_for_existing_role(iam_role_name, environmentUri,
                                                                                AWSAccountId)

        # if it exists, we just attach it
        else:
            # let's attach missing policy
            try:
                log.info('Let`s attach missing policies')
                IAM.attach_role_policy(
                    AWSAccountId,
                    iam_role_name,
                    share_policy['Arn']
                )
            except Exception as e:
                raise Exception(
                    f"Required customer managed policy {share_policy_name} can't be attached: {e}")

    @staticmethod
    def empty_share_policy_document():
        return {
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

    @staticmethod
    def remove_empty_statement(policy_doc):
        # toDo somehow remove this fake statement in more elegant way
        fake_statement = "arn:aws:s3:::initial-fake-empty-bucket"
        if fake_statement in policy_doc["Statement"][0]["Resource"]:
            policy_doc["Statement"][0]["Resource"].remove("arn:aws:s3:::initial-fake-empty-bucket")

    @staticmethod
    def create_managed_share_policies_for_role(environmentUri, AWSAccountId, iam_role_name, dataallManaged):
        empty_policy = SharePolicyService.empty_share_policy_document()
        policy_name = SharePolicyService.generate_share_policy_name(environmentUri, iam_role_name)

        IAM.create_managed_policy(
            account_id=AWSAccountId,
            policy_name=policy_name,
            policy=json.dumps(empty_policy)
        )

        if dataallManaged:
            IAM.attach_role_policy(
                account_id=AWSAccountId,
                role_name=iam_role_name,
                policy_arn=policy_name
            )

    @staticmethod
    def delete_managed_share_policies(environmentUri, AWSAccountId, iam_role_name):
        policy_name = SharePolicyService.generate_share_policy_name(environmentUri, iam_role_name)

        IAM.detach_policy_from_role(
            account_id=AWSAccountId,
            role_name=iam_role_name,
            policy_name=policy_name
        )

        IAM.delete_managed_policy_by_name(
            account_id=AWSAccountId,
            policy_name=policy_name
        )

    @staticmethod
    def get_resources_from_existing_inline_policy(AWSAccountId, iam_role_name, inline_policy_name):
        try:
            existing_policy = IAM.get_role_policy(
                AWSAccountId,
                iam_role_name,
                inline_policy_name
            )
            return existing_policy["Statement"][0]["Resource"]
        except Exception as e:
            log.error(
                f'Failed to retrieve the existing policy {inline_policy_name}: {e} '
            )
            return []

    @staticmethod
    def fill_policy_with_existing_resources(AWSAccountId, iam_role_name, policy_doc):
        new_resources = []
        new_resources.extend(SharePolicyService.get_resources_from_existing_inline_policy(
            AWSAccountId, iam_role_name, IAM_S3BUCKET_ROLE_POLICY
        ))
        new_resources.extend(SharePolicyService.get_resources_from_existing_inline_policy(
            AWSAccountId, iam_role_name, IAM_ACCESS_POINT_ROLE_POLICY
        ))
        policy_doc["Statement"][0]["Resource"] = new_resources
        SharePolicyService.remove_empty_statement(policy_doc)



    @staticmethod
    def delete_obsolete_inline_policies(AWSAccountId, iam_role_name):
        IAM.delete_role_policy(AWSAccountId, iam_role_name, IAM_ACCESS_POINT_ROLE_POLICY)
        IAM.delete_role_policy(AWSAccountId, iam_role_name, IAM_S3BUCKET_ROLE_POLICY)
