from aws_cdk import aws_iam as iam
import uuid
import hashlib


def get_tooling_account_external_id(account: str):
    return hashlib.md5(str(account).encode('UTF-8')).hexdigest()[:12]


def set_trust_policy_tooling_account(role: iam.Role, account: str, overwrite: bool = True) -> None:
    policy_statement = iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        principals=[iam.AccountPrincipal(account)],
        actions=['sts:AssumeRole'],
        conditions={
            'StringEquals': {'sts:ExternalId': get_tooling_account_external_id(account)},
        },
    )
    if overwrite:
        role.assume_role_policy = iam.PolicyDocument(statements=[policy_statement])
    else:
        role.assume_role_policy.add_statements(policy_statement)
