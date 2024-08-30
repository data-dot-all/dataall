import pytest

from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.core.environment.queries import invite_group_on_env, list_environments
from tests_new.integration_tests.core.organizations.queries import invite_team_to_organization, list_organizations
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


def ensure_group_invited(client, env, target_group, target_client):
    envs = [node.environmentUri for node in list_environments(target_client).nodes]
    if env.environmentUri not in envs:
        orgs = [node.organizationUri for node in list_organizations(target_client).nodes]
        print('ORGS = ', list_organizations(target_client))
        if env.organization.organizationUri not in orgs:
            invite_team_to_organization(client, env.organization.organizationUri, target_group)
        invite_group_on_env(client, env.environmentUri, target_group, [" UPDATE_ENVIRONMENT",
                                                                       "GET_ENVIRONMENT",
                                                                       "DELETE_ENVIRONMENT",
                                                                       "INVITE_ENVIRONMENT_GROUP",
                                                                       "REMOVE_ENVIRONMENT_GROUP",
                                                                       "UPDATE_ENVIRONMENT_GROUP",
                                                                       "LIST_ENVIRONMENT_GROUP_PERMISSIONS",
                                                                       "ADD_ENVIRONMENT_CONSUMPTION_ROLES",
                                                                       "LIST_ENVIRONMENT_CONSUMPTION_ROLES",
                                                                       "LIST_ENVIRONMENT_GROUPS",
                                                                       "CREDENTIALS_ENVIRONMENT",
                                                                       "ENABLE_ENVIRONMENT_SUBSCRIPTIONS",
                                                                       "DISABLE_ENVIRONMENT_SUBSCRIPTIONS",
                                                                       "CREATE_NETWORK",
                                                                       "LIST_ENVIRONMENT_NETWORKS"])


@pytest.fixture(scope='session')
def session_share_1(client5, client1,  persistent_env1, persistent_s3_dataset1, group5):
    ensure_group_invited(client1, persistent_env1, group5, client5)
    share1 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_s3_dataset1.datasetUri},
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
def session_share_2(client5, client1, persistent_env1, persistent_imported_sse_s3_dataset1, group5):
    ensure_group_invited(client1, persistent_env1, group5, client5)
    share2 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_imported_sse_s3_dataset1.datasetUri},
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
