import pytest
from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.s3_datasets.aws_clients import LakeFormationClient
from integration_tests.modules.shares.s3_datasets_shares.global_conftest import clean_up_share
from tests_new.integration_tests.modules.shares.queries import (
    create_share_object,
    submit_share_object,
    add_share_item,
    get_share_object,
    reject_share_object,
    delete_share_object,
    update_share_request_reason,
    update_share_reject_reason,
    reapply_items_share_object,
)
from tests_new.integration_tests.modules.shares.s3_datasets_shares.shared_test_functions import (
    check_share_items_access,
    check_verify_share_items,
    revoke_and_check_all_shared_items,
    check_all_items_revoke_job_succeeded,
    add_all_items_to_share,
    check_submit_share_object,
    check_approve_share_object,
    check_share_succeeded,
)
from tests_new.integration_tests.modules.shares.utils import (
    check_share_ready,
    check_share_items_reapplied,
)


def test_create_and_delete_share_object(new_share_param):
    client, group, dataset, env, principal_id, principal_type = new_share_param
    share = create_share_object(
        client=client,
        dataset_or_item_params={'datasetUri': dataset.datasetUri},
        environmentUri=env.environmentUri,
        groupUri=group,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(share.status).is_equal_to('Draft')
    delete_share_object(client, share.shareUri)


def test_submit_empty_object(new_share_param):
    # here Exception is not recognized as GqlError, so we use base class
    # toDo: back to GqlError
    client, group, dataset, env, principal_id, principal_type = new_share_param
    share = create_share_object(
        client=client,
        dataset_or_item_params={'datasetUri': dataset.datasetUri},
        environmentUri=env.environmentUri,
        groupUri=group,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(submit_share_object).raises(Exception).when_called_with(client, share.shareUri).contains(
        'ShareItemsFound', 'The request is empty'
    )
    clean_up_share(client, share.shareUri)


def test_add_share_items(new_share_param):
    client, group, dataset, env, principal_id, principal_type = new_share_param
    share = create_share_object(
        client=client,
        dataset_or_item_params={'datasetUri': dataset.datasetUri},
        environmentUri=env.environmentUri,
        groupUri=group,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    share_item_uri = add_share_item(client, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    assert_that(share_item_uri).is_not_none()

    updated_share = get_share_object(client, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).is_length(1)
    assert_that(items[0].shareItemUri).is_equal_to(share_item_uri)
    assert_that(items[0].status).is_equal_to('PendingApproval')

    clean_up_share(client, share.shareUri)


def test_reject_share(client1, new_share_param):
    client, group, dataset, env, principal_id, principal_type = new_share_param
    share = create_share_object(
        client=client,
        dataset_or_item_params={'datasetUri': dataset.datasetUri},
        environmentUri=env.environmentUri,
        groupUri=group,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    add_share_item(client, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    submit_share_object(client, share.shareUri)

    reject_share_object(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri)
    assert_that(updated_share.status).is_equal_to('Rejected')

    change_request_purpose = update_share_reject_reason(client1, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client, share.shareUri)
    assert_that(updated_share.rejectPurpose).is_equal_to('new purpose')

    clean_up_share(client, share.shareUri)


def test_change_share_purpose(share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    change_request_purpose = update_share_request_reason(client, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client, share.shareUri)
    assert_that(updated_share.requestPurpose).is_equal_to('new purpose')


@pytest.mark.dependency(name='share_submitted')
def test_submit_object(share_params_all):
    client, share, dataset = share_params_all
    add_all_items_to_share(client, share.shareUri)
    check_submit_share_object(client, share.shareUri, dataset)


@pytest.mark.dependency(name='share_approved', depends=['share_submitted'])
def test_approve_share(client1, share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    check_approve_share_object(client1, share.shareUri)


@pytest.mark.dependency(name='share_succeeded', depends=['share_approved'])
def test_share_succeeded(client1, share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    check_share_succeeded(client1, share.shareUri, check_contains_all_item_types=True)


@pytest.mark.dependency(name='share_verified', depends=['share_succeeded'])
def test_verify_share_items(client1, share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    check_verify_share_items(client1, share.shareUri)


@pytest.mark.dependency(depends=['share_verified'])
def test_check_item_access(share_params_main):
    client, group, env, env_client, role, share, _, _ = share_params_main
    check_share_items_access(client, group, share.shareUri, env, role, env_client)


@pytest.mark.dependency(name='unhealthy_items', depends=['share_verified'])
def test_unhealthy_items(share_params_main):
    client, group, env, env_client, role, share, _, integration_role_arn = share_params_main
    iam = env_client.resource('iam')
    principal_role = iam.Role(share.principal.principalRoleName)
    # break s3 by removing policies
    for policy in principal_role.attached_policies.all():
        if '/dataall-env-' in policy.arn and 'share-policy' in policy.arn:
            principal_role.detach_policy(PolicyArn=policy.arn)
    # break lf by removing DESCRIBE perms from principal
    lf_client = LakeFormationClient(env_client, env_client.region_name)
    lf_client.add_role_to_datalake_admin(integration_role_arn)
    db_name = f'dataall_{share.dataset.datasetName}_{share.dataset.datasetUri}_shared'.replace('-', '_')
    lf_client.revoke_db_perms(principal_role.arn, db_name, ['DESCRIBE'])
    # verify all items are `Unhealthy`
    check_verify_share_items(
        client,
        share.shareUri,
        expected_health_status=['Unhealthy'],
        expected_health_msg=[
            'IAM Policy attached Target Resource does not exist',
            'missing LF permissions: DESCRIBE',
        ],
    )


@pytest.mark.dependency(depends=['share_approved'])
def test_reapply_unauthoried(share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    share_uri = share.shareUri
    share_object = get_share_object(client, share_uri)
    item_uris = [item.shareItemUri for item in share_object['items'].nodes]
    assert_that(reapply_items_share_object).raises(GqlError).when_called_with(client, share_uri, item_uris).contains(
        'UnauthorizedOperation'
    )


@pytest.mark.dependency(depends=['share_approved'])
def test_reapply(client1, share_params_main):
    _, _, _, _, _, share, _, _ = share_params_main
    share_uri = share.shareUri
    share_object = get_share_object(client1, share_uri)
    item_uris = [item.shareItemUri for item in share_object['items'].nodes]
    reapply_items_share_object(client1, share_uri, item_uris)
    share_object = get_share_object(client1, share_uri)
    assert_that(share_object['items'].nodes).extracting('healthStatus').contains_only('PendingReApply')
    check_share_items_reapplied(client1, share_uri)
    check_verify_share_items(client1, share_uri)


@pytest.mark.dependency(name='share_revoked', depends=['share_succeeded'])
def test_revoke_share(share_params_main):
    client, _, _, _, _, share, _, _ = share_params_main
    check_share_ready(client, share.shareUri)
    revoke_and_check_all_shared_items(client, share.shareUri, check_contains_all_item_types=True)


@pytest.mark.dependency(name='share_revoke_succeeded', depends=['share_revoked'])
def test_revoke_succeeded(client1, share_params_main):
    client, group, env, env_client, role, share, dataset, _ = share_params_main
    check_all_items_revoke_job_succeeded(client, share.shareUri, check_contains_all_item_types=True)
    check_share_items_access(
        client,
        group,
        share.shareUri,
        env,
        role,
        env_client,
    )
