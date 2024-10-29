from assertpy import assert_that
import pytest

from integration_tests.errors import GqlError
from integration_tests.modules.shares.utils import (
    check_share_ready,
    check_share_items_verified,
    check_share_items_reapplied,
)
from integration_tests.modules.shares.queries import (
    approve_share_object,
    get_share_object,
    create_share_object,
    revoke_share_items,
    verify_share_items,
    reapply_share_items,
)
from integration_tests.modules.shares.redshift_datasets_shares.conftest import (
    REDSHIFT_TEST_ROLE_NAME,
    REDSHIFT_PRINCIPAL_TYPE,
    REDSHIFT_ITEM_TYPE,
)
from integration_tests.modules.shares.redshift_datasets_shares.aws_clients import RedshiftClient


@pytest.mark.parametrize(
    'share_object_fixture_name',
    [
        pytest.param(
            'submitted_redshift_share_request_source_serverless',
            marks=pytest.mark.dependency(name='serverless_share_submitted'),
        ),
        pytest.param(
            'submitted_redshift_share_request_source_cluster',
            marks=pytest.mark.dependency(name='cluster_share_submitted'),
        ),
    ],
)
def test_creation_submission_redshift_share(share_object_fixture_name, request):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    assert_that(share.status).is_equal_to('Draft')
    assert_that(share.shareUri).is_not_none()
    assert_that(share_item_uri).is_not_none()


@pytest.mark.parametrize(
    'client_name,share_object_fixture_name',
    [
        pytest.param(
            'client1',
            'submitted_redshift_share_request_source_serverless',
            marks=pytest.mark.dependency(name='serverless_share_approved', depends=['serverless_share_submitted']),
        ),
        pytest.param(
            'client5',
            'submitted_redshift_share_request_source_cluster',
            marks=pytest.mark.dependency(name='cluster_share_approved', depends=['cluster_share_submitted']),
        ),
    ],
)
def test_approve_redshift_share(client_name, share_object_fixture_name, request):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    client = request.getfixturevalue(client_name)
    approve_share_object(client=client, shareUri=share.shareUri)
    # Wait until share is processed
    check_share_ready(client=client, shareUri=share.shareUri)
    updated_share = get_share_object(client, share.shareUri, {'isShared': True})
    items = updated_share['items']
    assert_that(updated_share.status).is_equal_to('Processed')
    assert_that(items.count).is_equal_to(1)
    assert_that(items.nodes[0].shareItemUri).is_equal_to(share_item_uri)
    assert_that(items.nodes[0].itemType).is_equal_to(REDSHIFT_ITEM_TYPE)
    assert_that(items.nodes[0].status).is_equal_to('Share_Succeeded')


@pytest.mark.parametrize(
    'client_name,share_object_fixture_name',
    [
        pytest.param(
            'client1',
            'submitted_redshift_share_request_source_serverless',
            marks=pytest.mark.dependency(
                name='serverless_share_verified_healthy', depends=['serverless_share_approved']
            ),
        ),
        pytest.param(
            'client5',
            'submitted_redshift_share_request_source_cluster',
            marks=pytest.mark.dependency(name='cluster_share_verified_healthy', depends=['cluster_share_approved']),
        ),
    ],
)
def test_verify_redshift_share_healthy(client_name, share_object_fixture_name, request):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    client = request.getfixturevalue(client_name)
    share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    last_verification_time = share['items'].nodes[0].lastVerificationTime
    verify_share_items(client=client, shareUri=share.shareUri, shareItemsUris=[share_item_uri])
    # Wait until verification task has completed
    check_share_items_verified(client=client, shareUri=share.shareUri)
    verified_share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    item = verified_share['items'].nodes[0]
    assert_that(item.healthStatus).is_equal_to('Healthy')
    assert_that(item.lastVerificationTime).is_not_equal_to(last_verification_time)


@pytest.mark.parametrize(
    'client_name,share_object_fixture_name,source_aws_client_name,source_env_name,target_env_name,source_connection_name,target_connection_name',
    [
        pytest.param(
            'client1',
            'submitted_redshift_share_request_source_serverless',
            'session_env1_aws_client',
            'session_env1',
            'session_cross_acc_env_1',
            'session_connection_serverless_admin',
            'session_connection_cluster_admin',
            marks=pytest.mark.dependency(
                name='serverless_share_verified_unhealthy', depends=['serverless_share_verified_healthy']
            ),
        ),
        pytest.param(
            'client5',
            'submitted_redshift_share_request_source_cluster',
            'session_cross_acc_env_1_aws_client',
            'session_cross_acc_env_1',
            'session_env1',
            'session_connection_cluster_admin',
            'session_connection_serverless_admin',
            marks=pytest.mark.dependency(
                name='cluster_share_verified_unhealthy', depends=['cluster_share_verified_healthy']
            ),
        ),
    ],
)
def test_verify_redshift_share_unhealthy(
    client_name,
    share_object_fixture_name,
    source_aws_client_name,
    source_env_name,
    target_env_name,
    source_connection_name,
    target_connection_name,
    request,
):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    client = request.getfixturevalue(client_name)
    source_aws_client = request.getfixturevalue(source_aws_client_name)
    source_env = request.getfixturevalue(source_env_name)
    target_env = request.getfixturevalue(target_env_name)
    source_connection = request.getfixturevalue(source_connection_name)
    target_connection = request.getfixturevalue(target_connection_name)
    share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    last_verification_time = share['items'].nodes[0].lastVerificationTime
    # Make the share item unhealthy by deauthorizing the datashare
    datashare_name = f'dataall_{target_connection.nameSpaceId}_{share.datasetUri}'
    clean_datashare_name = datashare_name.replace('-', '_')
    datashare_arn = f'arn:aws:redshift:{source_env.region}:{source_env.AwsAccountId}:datashare:{source_connection.nameSpaceId}/{clean_datashare_name}'
    RedshiftClient(session=source_aws_client, region=source_env.region).deauthorize_datashare(
        datashare_arn=datashare_arn, target_account=target_env.get('AwsAccountId')
    )
    verify_share_items(client=client, shareUri=share.shareUri, shareItemsUris=[share_item_uri])
    # Wait until verification task has completed
    check_share_items_verified(client=client, shareUri=share.shareUri)
    verified_share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    item = verified_share['items'].nodes[0]
    assert_that(item.healthStatus).is_equal_to('Unhealthy')
    assert_that(item.lastVerificationTime).is_not_equal_to(last_verification_time)


@pytest.mark.parametrize(
    'client_name,share_object_fixture_name',
    [
        pytest.param(
            'client1',
            'submitted_redshift_share_request_source_serverless',
            marks=pytest.mark.dependency(
                name='serverless_share_reapply', depends=['serverless_share_verified_unhealthy']
            ),
        ),
        pytest.param(
            'client5',
            'submitted_redshift_share_request_source_cluster',
            marks=pytest.mark.dependency(name='cluster_share_reapply', depends=['cluster_share_verified_unhealthy']),
        ),
    ],
)
def test_reapply_redshift_share(client_name, share_object_fixture_name, request):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    client = request.getfixturevalue(client_name)
    share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    ## reapply share item
    reapply_share_items(client=client, shareUri=share.shareUri, shareItemsUris=[share_item_uri])
    # Wait until reapply task has completed
    check_share_items_reapplied(client=client, shareUri=share.shareUri)
    ## Verify again
    verify_share_items(client=client, shareUri=share.shareUri, shareItemsUris=[share_item_uri])
    # Wait until verification task has completed
    check_share_items_verified(client=client, shareUri=share.shareUri)
    verified_share = get_share_object(client=client, shareUri=share.shareUri, filter={'isShared': True})
    item = verified_share['items'].nodes[0]
    assert_that(item.healthStatus).is_equal_to('Healthy')


@pytest.mark.parametrize(
    'client_name,share_object_fixture_name',
    [
        pytest.param(
            'client1',
            'submitted_redshift_share_request_source_serverless',
            marks=pytest.mark.dependency(name='serverless_share_revoked', depends=['serverless_share_reapply']),
        ),
        pytest.param(
            'client5',
            'submitted_redshift_share_request_source_cluster',
            marks=pytest.mark.dependency(name='cluster_share_revoked', depends=['cluster_share_reapply']),
        ),
    ],
)
def test_revoke_redshift_share(client_name, share_object_fixture_name, request):
    share, share_item_uri = request.getfixturevalue(share_object_fixture_name)
    client = request.getfixturevalue(client_name)
    revoke_share_items(client=client, shareUri=share.shareUri, shareItemUris=[share_item_uri])
    # Wait until share is processed
    check_share_ready(client=client, shareUri=share.shareUri)
    updated_share = get_share_object(client, share.shareUri, {'isShared': True})
    items = updated_share['items']
    assert_that(updated_share.status).is_equal_to('Processed')
    assert_that(items.count).is_equal_to(1)
    assert_that(items.nodes[0].status).is_equal_to('Revoke_Succeeded')


def test_create_redshift_share_invalid_target_connection(
    client5, group5, session_cross_acc_env_1, session_connection_cluster_data_user, session_redshift_dataset_serverless
):
    # DATA_USER connections cannot be used as target connection for a share. Even if used by the connection owners.
    # it checks that there are no CREATE_SHARE_REQUEST_WITH_CONNECTION on the connection
    assert_that(create_share_object).raises(GqlError).when_called_with(
        client=client5,
        dataset_or_item_params={'datasetUri': session_redshift_dataset_serverless.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalRoleName=REDSHIFT_TEST_ROLE_NAME,
        principalId=session_connection_cluster_data_user.connectionUri,
        principalType=REDSHIFT_PRINCIPAL_TYPE,
        requestPurpose='Integration tests - Redshift shares',
        attachMissingPolicies=False,
        permissions=['Read'],
    ).contains(
        'UnauthorizedOperation',
        'CREATE_SHARE_REQUEST_WITH_CONNECTION',
        session_connection_cluster_data_user.connectionUri,
    )


def test_create_redshift_share_invalid_redshift_role(
    client5, group5, session_cross_acc_env_1, session_connection_cluster_admin, session_redshift_dataset_serverless
):
    assert_that(create_share_object).raises(GqlError).when_called_with(
        client=client5,
        dataset_or_item_params={'datasetUri': session_redshift_dataset_serverless.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalRoleName='doesnotexist',
        principalId=session_connection_cluster_admin.connectionUri,
        principalType=REDSHIFT_PRINCIPAL_TYPE,
        requestPurpose='Integration tests - Redshift shares',
        attachMissingPolicies=False,
        permissions=['Read'],
    ).contains('PrincipalRoleNotFound', 'doesnotexist', session_connection_cluster_admin.name)
