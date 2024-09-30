import json

import boto3

from tests_new.integration_tests.aws_clients.sts import StsClient
from tests_new.integration_tests.core.environment.queries import get_environment_access_token
from tests_new.integration_tests.modules.share_base.queries import get_share_object
from tests_new.integration_tests.utils import poller


def is_share_in_progress(share):
    return share.status in [
        'Share_In_Progress',
        'Revoke_In_Progress',
        'Approved',
        'Revoked',
    ]


def is_all_items_verified(share):
    items = share['items'].nodes
    statuses = [item.healthStatus for item in items]
    return not ('PendingVerify' in statuses or 'PendingReApply' in statuses)


@poller(check_success=lambda share: not is_share_in_progress(share), timeout=600)
def check_share_ready(client, shareUri):
    return get_share_object(client, shareUri)


@poller(check_success=lambda share: is_all_items_verified(share), timeout=600)
def check_share_items_verified(client, shareUri):
    return get_share_object(client, shareUri)


def get_group_session(client, env_uri, group):
    credentials = json.loads(get_environment_access_token(client, env_uri, group))

    return boto3.Session(
        aws_access_key_id=credentials['AccessKey'],
        aws_secret_access_key=credentials['SessionKey'],
        aws_session_token=credentials['sessionToken'],
    )


def get_role_session(session, role_arn, region):
    sts_client = StsClient(session=session, region=region)
    return sts_client.get_role_session(role_arn)
