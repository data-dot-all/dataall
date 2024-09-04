from aws_cdk import aws_iam as iam
import uuid
import hashlib


def get_tooling_account_external_id(account: str):
    return hashlib.md5(str(account).encode('UTF-8')).hexdigest()[:12]


def set_trust_policy_tooling_account(role: iam.Role, account: str) -> None:
    role.assume_role_policy.add_statements(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AccountPrincipal(account)],
            actions=['sts:AssumeRole'],
            conditions={
                'StringEquals': {'sts:ExternalId': get_tooling_account_external_id(account)},
            },
        )
    )
