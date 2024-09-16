import re

from tests_new.integration_tests.modules.share_base.queries import get_share_object
from tests_new.integration_tests.utils import poller
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus, ShareItemHealthStatus


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
