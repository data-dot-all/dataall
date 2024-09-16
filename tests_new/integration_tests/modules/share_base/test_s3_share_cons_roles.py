from assertpy import assert_that
import pytest

from dataall.modules.shares_base.services.shares_enums import (
    PrincipalType,
    ShareObjectStatus,
    ShareItemStatus,
    ShareItemHealthStatus,
    ShareableType,
)
from tests_new.integration_tests.modules.share_base.utils import check_share_ready, check_share_items_verified
from tests_new.integration_tests.modules.share_base.conftest import clean_up_share
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    delete_share_object,
    submit_share_object,
    get_share_object,
    add_share_item,
    reject_share_object,
    update_share_reject_reason,
    update_share_request_reason,
    approve_share_object,
    verify_share_items,
    revoke_share_items,
)


def test_create_and_delete_share_object(
    client5, persistent_cross_acc_env_1, consumption_role_1, session_s3_dataset1, group5
):
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(share.status).is_equal_to(ShareObjectStatus.Draft.value)
    delete_share_object(client5, share.shareUri)


def test_submit_empty_object(client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, consumption_role_1):
    # here Exception is not recognized as GqlError, so we use base class
    # toDo: back to GqlError
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(submit_share_object).raises(Exception).when_called_with(client5, share.shareUri).contains(
        'ShareItemsFound', 'The request is empty'
    )
    clean_up_share(client5, share.shareUri)


def test_add_share_items(client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, consumption_role_1):
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client5, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    share_item_uri = add_share_item(client5, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    assert_that(share_item_uri).is_not_none()

    updated_share = get_share_object(client5, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).is_length(1)
    assert_that(items[0].shareItemUri).is_equal_to(share_item_uri)
    assert_that(items[0].status).is_equal_to(ShareItemStatus.PendingApproval.value)

    clean_up_share(client5, share.shareUri)


def test_reject_share(client1, client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, consumption_role_1):
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client5, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    add_share_item(client5, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    submit_share_object(client5, share.shareUri)

    reject_share_object(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Rejected.value)

    change_request_purpose = update_share_reject_reason(client1, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client5, share.shareUri)
    assert_that(updated_share.rejectPurpose).is_equal_to('new purpose')

    clean_up_share(client5, share.shareUri)


def test_change_share_purpose(client5, session_share_consrole_1):
    change_request_purpose = update_share_request_reason(client5, session_share_consrole_1.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client5, session_share_consrole_1.shareUri)
    assert_that(updated_share.requestPurpose).is_equal_to('new purpose')


@pytest.mark.dependency()
def test_submit_object_no_auto_approval(client5, session_share_consrole_1):
    items = session_share_consrole_1['items'].nodes
    for item in items:
        add_share_item(client5, session_share_consrole_1.shareUri, item.itemUri, item.itemType)

    submit_share_object(client5, session_share_consrole_1.shareUri)
    updated_share = get_share_object(client5, session_share_consrole_1.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Submitted.value)


def test_submit_object_with_auto_approval(client5, session_share_consrole_2):
    items = session_share_consrole_2['items'].nodes
    item_to_add = items[0]
    add_share_item(client5, session_share_consrole_2.shareUri, item_to_add.itemUri, item_to_add.itemType)

    submit_share_object(client5, session_share_consrole_2.shareUri)
    updated_share = get_share_object(client5, session_share_consrole_2.shareUri)
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)


@pytest.mark.dependency(depends=['test_submit_object_no_auto_approval'])
def test_approve_share(client1, session_share_consrole_1):
    approve_share_object(client1, session_share_consrole_1.shareUri)

    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)
    items = updated_share['items'].nodes
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Share_Approved.value)


@pytest.mark.dependency(depends=['test_approve_share'])
def test_share_succeeded(client1, session_share_consrole_1):
    check_share_ready(client1, session_share_consrole_1.shareUri)
    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Share_Succeeded.value)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Healthy.value)
    assert_that(items).extracting('itemType').contains(ShareableType.Table.name)
    assert_that(items).extracting('itemType').contains(ShareableType.S3Bucket.name)
    assert_that(items).extracting('itemType').contains(ShareableType.StorageLocation.name)


@pytest.mark.dependency(depends=['test_share_succeeded'])
def test_verify_share_items(client1, session_share_consrole_1):
    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    times = {}
    for item in items:
        times[item.shareItemUri] = item.lastVerificationTime
    verify_share_items(client1, session_share_consrole_1.shareUri, [item.shareItemUri for item in items])
    check_share_items_verified(client1, session_share_consrole_1.shareUri)
    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Share_Succeeded.value)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Healthy.value)
        assert_that(item.lastVerificationTime).is_not_equal_to(times[item.shareItemUri])


@pytest.mark.dependency(depends=['test_share_succeeded'])
def test_revoke_share(client1, session_share_consrole_1):
    check_share_ready(client1, session_share_consrole_1.shareUri)
    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    shareItemUris = [item.shareItemUri for item in items]
    revoke_share_items(client1, session_share_consrole_1.shareUri, shareItemUris)

    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Revoked.value)
    items = updated_share['items'].nodes
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Revoke_Approved.value)
    assert_that(items).extracting('itemType').contains(ShareableType.Table.name)
    assert_that(items).extracting('itemType').contains(ShareableType.S3Bucket.name)
    assert_that(items).extracting('itemType').contains(ShareableType.StorageLocation.name)


@pytest.mark.dependency(depends=['test_revoke_share'])
def test_revoke_succeeded(client1, session_share_consrole_1):
    check_share_ready(client1, session_share_consrole_1.shareUri)
    updated_share = get_share_object(client1, session_share_consrole_1.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Revoke_Succeeded.value)
    assert_that(items).extracting('itemType').contains(ShareableType.Table.name)
    assert_that(items).extracting('itemType').contains(ShareableType.S3Bucket.name)
    assert_that(items).extracting('itemType').contains(ShareableType.StorageLocation.name)
