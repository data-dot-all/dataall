import pytest
from assertpy import assert_that

from tests_new.integration_tests.aws_clients.athena import AthenaClient
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemStatus,
    ShareObjectStatus,
    ShareItemHealthStatus,
    ShareableType,
)
from tests_new.integration_tests.modules.s3_datasets.aws_clients import S3Client
from tests_new.integration_tests.modules.share_base.conftest import clean_up_share
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    submit_share_object,
    add_share_item,
    get_share_object,
    reject_share_object,
    approve_share_object,
    revoke_share_items,
    delete_share_object,
    verify_share_items,
    update_share_request_reason,
    update_share_reject_reason,
    get_s3_consumption_data,
)
from tests_new.integration_tests.modules.share_base.utils import (
    check_share_ready,
    check_share_items_verified,
    get_group_session,
    get_role_session,
)

ALL_S3_SHARABLE_TYPES_NAMES = [
    ShareableType.Table.name,
    ShareableType.StorageLocation.name,
    ShareableType.S3Bucket.name,
]


def test_create_and_delete_share_object(client5, persistent_cross_acc_env_1, session_s3_dataset1, principal1, group5):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(share.status).is_equal_to(ShareObjectStatus.Draft.value)
    delete_share_object(client5, share.shareUri)


def test_submit_empty_object(client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    # here Exception is not recognized as GqlError, so we use base class
    # toDo: back to GqlError
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(submit_share_object).raises(Exception).when_called_with(client5, share.shareUri).contains(
        'ShareItemsFound', 'The request is empty'
    )
    clean_up_share(client5, share.shareUri)


def test_add_share_items(client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
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


def test_reject_share(client1, client5, persistent_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
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


def test_change_share_purpose(client5, share_params_main):
    share, dataset = share_params_main
    change_request_purpose = update_share_request_reason(client5, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client5, share.shareUri)
    assert_that(updated_share.requestPurpose).is_equal_to('new purpose')


@pytest.mark.dependency(name='share_submitted')
def test_submit_object(client5, share_params_all):
    share, dataset = share_params_all
    updated_share = get_share_object(client5, share.shareUri)
    items = updated_share['items'].nodes
    for item in items:
        add_share_item(client5, share.shareUri, item.itemUri, item.itemType)

    submit_share_object(client5, share.shareUri)
    updated_share = get_share_object(client5, share.shareUri)
    if dataset.autoApprovalEnabled:
        assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)
    else:
        assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Submitted.value)


@pytest.mark.dependency(name='share_approved', depends=['share_submitted'])
def test_approve_share(client1, share_params_main):
    share, dataset = share_params_main
    approve_share_object(client1, share.shareUri)

    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Approved.value)
    items = updated_share['items'].nodes
    assert_that(items).extracting('status').contains_only(ShareItemStatus.Share_Approved.value)


@pytest.mark.dependency(name='share_succeeded', depends=['share_approved'])
def test_share_succeeded(client1, share_params_main):
    share, dataset = share_params_main
    check_share_ready(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    for item in items:
        assert_that(item.status).is_equal_to(ShareItemStatus.Share_Succeeded.value)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Healthy.value)
    assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)


@pytest.mark.dependency(name='share_verified', depends=['share_succeeded'])
def test_verify_share_items(client1, share_params_main):
    share, dataset = share_params_main
    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    times = [item.lastVerificationTime for item in items]
    verify_share_items(client1, share.shareUri, [item.shareItemUri for item in items])
    check_share_items_verified(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).extracting('status').contains_only(ShareItemStatus.Share_Succeeded.value)
    assert_that(items).extracting('healthStatus').contains_only(ShareItemHealthStatus.Healthy.value)
    assert_that(items).extracting('lastVerificationTime').does_not_contain(*times)


@pytest.mark.dependency(depends=['share_verified'])
def test_check_item_access(
    client5, persistent_cross_acc_env_1_aws_client, share_params_main, group5, consumption_role_1
):
    share, dataset = share_params_main
    principal_type = share.principal.principalType
    if principal_type == 'Group':
        session = get_group_session(client5, share.environment.environmentUri, group5)
    elif principal_type == 'ConsumptionRole':
        session = get_role_session(persistent_cross_acc_env_1_aws_client, consumption_role_1.IAMRoleArn, dataset.region)
    else:
        raise Exception('wrong principal type')

    s3_client = S3Client(session, dataset.region)
    athena_client = AthenaClient(session, dataset.region)

    consumption_data = get_s3_consumption_data(client5, share.shareUri)
    updated_share = get_share_object(client5, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    glue_db = consumption_data.sharedGlueDatabase
    access_point_arn = (
        f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{consumption_data.s3AccessPointName}'
    )
    if principal_type == 'Group':
        workgroup = athena_client.get_env_work_group(updated_share.environment.name)
        athena_workgroup_output_location = ''
    else:
        workgroup = 'primary'
        athena_workgroup_output_location = (
            f's3://dataset-{dataset.datasetUri}-session-query-results/athenaqueries/primary/'
        )

    for item in items:
        if item.itemType == ShareableType.Table.name:
            # nosemgrep-next-line:noexec
            query = 'SELECT * FROM {}.{}'.format(glue_db, item.itemName)
            if principal_type == 'Group':
                q_id = athena_client.run_query(query, workgroup=workgroup)
            else:
                q_id = athena_client.run_query(query, output_location=athena_workgroup_output_location)
            state = athena_client.wait_for_query(q_id)
            assert_that(state).is_equal_to('SUCCEEDED')
        elif item.itemType == ShareableType.S3Bucket.name:
            assert_that(s3_client.bucket_exists(item.itemName)).is_not_none()
            assert_that(s3_client.list_bucket_objects(item.itemName)).is_not_none()
        elif item.itemType == ShareableType.StorageLocation.name:
            assert_that(s3_client.list_accesspoint_folder_objects(access_point_arn, item.itemName + '/')).is_not_none()


@pytest.mark.dependency(name='share_revoked', depends=['share_succeeded'])
def test_revoke_share(client1, share_params_main):
    share, dataset = share_params_main
    check_share_ready(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    shareItemUris = [item.shareItemUri for item in items]
    revoke_share_items(client1, share.shareUri, shareItemUris)

    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Revoked.value)
    items = updated_share['items'].nodes

    assert_that(items).extracting('status').contains_only(ShareItemStatus.Revoke_Approved.value)
    assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)


@pytest.mark.dependency(name='share_revoke_succeeded', depends=['share_revoked'])
def test_revoke_succeeded(client1, share_params_main):
    share, dataset = share_params_main
    check_share_ready(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to(ShareObjectStatus.Processed.value)
    assert_that(items).extracting('status').contains_only(ShareItemStatus.Revoke_Succeeded.value)
    assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)
