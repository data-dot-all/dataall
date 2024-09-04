from aws_cdk import aws_iam as iam
import uuid
import hashlib


def get_tooling_account_external_id(account: str):
    return hashlib.md5(str(account).encode('UTF-8')).hexdigest()[:12]
