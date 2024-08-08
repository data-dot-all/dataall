import re

from tests_new.integration_tests.modules.share_base.queries import get_share_object
from tests_new.integration_tests.utils import poller
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus


def is_share_in_progress(share):
    return share.status in [
        ShareObjectStatus.Share_In_Progress.value,
        ShareObjectStatus.Revoke_In_Progress.value,
        ShareObjectStatus.Approved.value,
        ShareObjectStatus.Revoked.value,
    ]


@poller(check_success=is_share_in_progress, timeout=200)
def check_share_in_progress(client, shareUri):
    return get_share_object(client, shareUri)


@poller(check_success=lambda share: not is_share_in_progress(share), timeout=600)
def check_share_ready(client, shareUri):
    return get_share_object(client, shareUri)
