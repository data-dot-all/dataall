import pytest

from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.core.environment.queries import invite_group_on_env, list_environments
from tests_new.integration_tests.core.organizations.queries import invite_team_to_organization, list_organizations
from tests_new.integration_tests.core.stack.utils import check_stack_ready
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
def session_share_1(client5, client1,  persistent_env1, persistent_s3_dataset_for_share_test, group5):
    share1 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_s3_dataset_for_share_test.datasetUri},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group5,
        principalId=group5,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share1 = get_share_object(client5, share1.shareUri)
    yield share1
    clean_up_share(client5, share1.shareUri)


@pytest.fixture(scope='session')
def session_share_2(client5, client1, persistent_env1, persistent_s3_dataset_for_share_test_autoapproval, group5):
    share2 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_s3_dataset_for_share_test_autoapproval.datasetUri},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group5,
        principalId=group5,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share2 = get_share_object(client5, share2.shareUri)
    yield share2

    clean_up_share(client5, share2.shareUri)
