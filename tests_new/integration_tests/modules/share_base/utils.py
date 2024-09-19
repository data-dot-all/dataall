import json
import re

import boto3

from tests_new.integration_tests.aws_clients.sts import StsClient
from tests_new.integration_tests.modules.share_base.queries import get_share_object
from tests_new.integration_tests.utils import poller
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus, ShareItemHealthStatus
from tests_new.integration_tests.core.environment.queries import get_environment_access_token


def is_share_in_progress(share):
    return share.status in [
        ShareObjectStatus.Share_In_Progress.value,
        ShareObjectStatus.Revoke_In_Progress.value,
        ShareObjectStatus.Approved.value,
        ShareObjectStatus.Revoked.value,
    ]


def is_all_items_verified(share):
    items = share['items'].nodes
    statuses = [item.healthStatus for item in items]
    return not (
        ShareItemHealthStatus.PendingVerify.value in statuses or ShareItemHealthStatus.PendingReApply.value in statuses
    )


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


def get_role_session(aws_profile, role_arn, region):
    sts_client = StsClient(session=None, profile=aws_profile, region=region)
    return sts_client.get_role_session(role_arn)
