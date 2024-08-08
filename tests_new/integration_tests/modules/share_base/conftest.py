import pytest

from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    delete_share_object,
    get_share_object,
    revoke_share_items,
)
from tests_new.integration_tests.modules.share_base.utils import check_share_ready
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus, ShareItemStatus


def revoke_all_possible(client, shareUri):
    share = get_share_object(client, shareUri, {'isShared': True})
    statuses_can_delete = [
        ShareItemStatus.PendingApproval.value,
        ShareItemStatus.Revoke_Succeeded.value,
        ShareItemStatus.Share_Failed.value,
        ShareItemStatus.Share_Rejected.value,
    ]

    shareItemUris = [item.shareItemUri for item in share['items'].nodes if item.status not in statuses_can_delete]
    if shareItemUris:
        revoke_share_items(client, shareUri, shareItemUris)


def clean_up_share(client, shareUri):
    check_share_ready(client, shareUri)
    revoke_all_possible(client, shareUri)
    check_share_ready(client, shareUri)
    delete_share_object(client, shareUri)


@pytest.fixture(scope='session')
def session_share_1(client2, persistent_env1, group2):
    share1 = create_share_object(
        client=client2,
        dataset_or_item_params={'datasetUri': 'b56r7soc'},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group2,
        principalId=group2,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share1 = get_share_object(client2, share1.shareUri)
    yield share1
    clean_up_share(client2, share1.shareUri)


@pytest.fixture(scope='session')
def session_share_2(client2, persistent_env1, group2):
    share2 = create_share_object(
        client=client2,
        dataset_or_item_params={'datasetUri': 'w0il0em5'},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group2,
        principalId=group2,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share2 = get_share_object(client2, share2.shareUri)
    yield share2

    clean_up_share(client2, share2.shareUri)
