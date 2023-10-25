from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam
from dataall.base.aws.kms import KmsClient
from dataall.base.aws.sts import SessionHelper
from dataall.base.utils.iam_policy_utils import split_policy_with_resources_in_statements


class KMSPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS KMS.
    It allows pivot role to:
    list and Describe KMS keys
    manage data.all created KMS keys
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='KMSList',
                effect=iam.Effect.ALLOW,
                actions=[
                    'kms:List*',
                    'kms:DescribeKey',
                ],
                resources=['*'],
            ),
        ]
        dataall_kms_keys = []
        kms_client = KmsClient(
            account_id=self.account,
            region=self.region,
            role=SessionHelper.get_cdk_look_up_role_arn(accountid=self.account, region=self.region)
        )
        key_aliases = kms_client.list_kms_alias(key_alias_prefix=self.env_resource_prefix)
        for alias in key_aliases:
            key_id = kms_client.get_key_id(
                key_alias=f"alias/{alias}"
            )
            if key_id:
                dataall_kms_keys.append(
                    f"arn:aws:kms:{self.region}:{self.account}:key/{key_id}")

        kms_statement = split_policy_with_resources_in_statements(
            base_sid='KMSDataallAccess',
            effect=iam.Effect.ALLOW,
            actions=[
                'kms:Decrypt',
                'kms:Encrypt',
                'kms:GenerateDataKey*',
                'kms:PutKeyPolicy',
                'kms:ReEncrypt*',
                'kms:TagResource',
                'kms:UntagResource',
            ],
            resources=dataall_kms_keys
        )
        statements.extend(kms_statement)
        return statements
