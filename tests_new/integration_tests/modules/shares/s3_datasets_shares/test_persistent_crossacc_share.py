from tests_new.integration_tests.modules.shares.utils import check_share_ready
from integration_tests.modules.shares.s3_datasets_shares.shared_test_functions import (
    check_share_items_access,
    check_verify_share_items,
    revoke_and_check_all_shared_items,
    check_all_items_revoke_job_succeeded,
    add_all_items_to_share,
    check_submit_share_object,
    check_approve_share_object,
    check_share_succeeded,
    delete_all_non_shared_items,
)

"""
1. Update persistent envs and datasets used for shares (made in fixtures)
2. Share verification test
3. Check item access test
4. Revoke share test
5. Check no access left
6. Add all items back to share
7. Share approved/processed successfully
8. Share verification test
9. Check item access test
"""


def test_verify_share_items(client5, persistent_share_params_main):
    share, _ = persistent_share_params_main
    check_verify_share_items(client5, share.shareUri)


def test_check_share_items_access(
    client5, group5, persistent_share_params_main, persistent_consumption_role_1, persistent_cross_acc_env_1_aws_client
):
    share, env = persistent_share_params_main
    check_share_items_access(
        client5,
        group5,
        share.shareUri,
        env,
        persistent_consumption_role_1,
        persistent_cross_acc_env_1_aws_client,
    )


def test_revoke_share(client1, persistent_share_params_main):
    share, _ = persistent_share_params_main
    check_share_ready(client1, share.shareUri)
    revoke_and_check_all_shared_items(client1, share.shareUri, check_contains_all_item_types=True)


def test_revoke_succeeded(
    client1,
    client5,
    group5,
    persistent_share_params_main,
    persistent_consumption_role_1,
    persistent_cross_acc_env_1_aws_client,
):
    share, env = persistent_share_params_main
    check_all_items_revoke_job_succeeded(client1, share.shareUri, check_contains_all_item_types=True)
    check_share_items_access(
        client5,
        group5,
        share.shareUri,
        env,
        persistent_consumption_role_1,
        persistent_cross_acc_env_1_aws_client,
    )


def test_delete_all_nonshared_items(client5, persistent_share_params_main):
    share, _ = persistent_share_params_main
    check_share_ready(client5, share.shareUri)
    delete_all_non_shared_items(client5, share.shareUri)


def test_add_items_back_to_share(client5, persistent_share_params_main):
    share, _ = persistent_share_params_main
    check_share_ready(client5, share.shareUri)
    add_all_items_to_share(client5, share.shareUri)


def test_submit_share(client5, persistent_share_params_main, persistent_s3_dataset1):
    share, _ = persistent_share_params_main
    check_submit_share_object(client5, share.shareUri, persistent_s3_dataset1)


def test_approve_share(client1, persistent_share_params_main):
    share, _ = persistent_share_params_main
    check_approve_share_object(client1, share.shareUri)


def test_re_share_succeeded(
    client5, persistent_share_params_main, persistent_consumption_role_1, persistent_cross_acc_env_1_aws_client
):
    share, env = persistent_share_params_main
    check_share_succeeded(client5, share.shareUri, check_contains_all_item_types=True)
    check_verify_share_items(client5, share.shareUri)
    check_share_items_access(
        client5,
        share.principal.SamlGroupName,
        share.shareUri,
        env,
        persistent_consumption_role_1,
        persistent_cross_acc_env_1_aws_client,
    )
