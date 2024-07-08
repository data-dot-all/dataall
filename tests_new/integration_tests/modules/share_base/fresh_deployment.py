from assertpy import assert_that

from dataall.modules.shares_base.services.shares_enums import ShareItemStatus, ShareObjectStatus
from tests_new.integration_tests.errors import GqlError

from tests_new.integration_tests.modules.share_base.queries import (
    submit_share_object,
    add_share_item,
    get_share_object,
    reject_share_object,
    approve_share_object,
    revoke_share_items,
)
from tests_new.integration_tests.modules.share_base.utils import check_share_ready


def test_create_share_object(share1):
    assert_that(share1.status).is_equal_to(ShareObjectStatus.Draft.value)


def test_submit_empty_object(client2, share1):
    # here Exception is not recognized as GqlError, so we use base class
    # toDo: back to GqlError
    assert_that(submit_share_object).raises(Exception).when_called_with(client2, share1.shareUri).contains(
        'ShareItemsFound', 'The request is empty'
    )


def test_add_share_items(client2, share1):
    items = share1['items'].nodes
    assert_that(items[0].status).is_none()
    assert_that(items).is_length(4)

    item_to_add = items[0]
    share_item_uri = add_share_item(client2, share1.shareUri, item_to_add.itemUri, item_to_add.itemType)
    assert_that(share_item_uri).is_not_none()

    updated_share = get_share_object(client2, share1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).is_length(1)
    assert_that(items[0].shareItemUri).is_equal_to(share_item_uri)
    assert_that(items[0].status).is_equal_to(ShareItemStatus.PendingApproval.value)


def test_submit_object_no_auto_approval(client2, share1):
    submit_share_object(client2, share1.shareUri)
    updated_share = get_share_object(client2, share1.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Submitted.value)


"""
def test_submit_object_with_auto_approval(client2, share2):
    items = share2['items'].nodes
    item_to_add = items[0]
    add_share_item(client2, share2.shareUri, item_to_add.itemUri, item_to_add.itemType)

    submit_share_object(client2, share2.shareUri)
    updated_share = get_share_object(client2, share2.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)
"""


def test_reject_share(client1, share1):
    reject_share_object(client1, share1.shareUri)
    updated_share = get_share_object(client1, share1.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Rejected.value)


def test_approve_share(client1, share3):
    approve_share_object(client1, share3.shareUri)
    updated_share = get_share_object(client1, share3.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)


def test_share_succeeded(client1, share3):
    check_share_ready(client1, share3.shareUri)
    updated_share = get_share_object(client1, share3.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Share_Succeeded.value)


def test_revoke_share(client1, share3):
    check_share_ready(client1, share3.shareUri)
    updated_share = get_share_object(client1, share3.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    shareItemUris = [item.shareItemUri for item in items]
    revoke_share_items(client1, share3.shareUri, shareItemUris)

    updated_share = get_share_object(client1, share3.shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Revoked.value)
    items = updated_share['items'].nodes
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Revoke_Approved.value)


def test_revoke_succeeded(client1, share3):
    check_share_ready(client1, share3.shareUri)
    updated_share = get_share_object(client1, share3.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Revoke_Succeeded.value)
