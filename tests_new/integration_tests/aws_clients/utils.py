import json
import boto3

from tests_new.integration_tests.aws_clients.sts import StsClient


def get_group_session(credentials_str):
    credentials = json.loads(credentials_str)
    return boto3.Session(
        aws_access_key_id=credentials['AccessKey'],
        aws_secret_access_key=credentials['SessionKey'],
        aws_session_token=credentials['sessionToken'],
    )


def get_role_session(session, role_arn, region):
    sts_client = StsClient(session=session, region=region)
    return sts_client.get_role_session(role_arn)
