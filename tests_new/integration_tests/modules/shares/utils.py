from tests_new.integration_tests.modules.shares.queries import get_share_object
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
