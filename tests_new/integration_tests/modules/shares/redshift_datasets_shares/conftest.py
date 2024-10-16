import logging
import pytest

from integration_tests.modules.shares.queries import (
    create_share_object,
    add_share_item,
    revoke_share_items,
    submit_share_object,
    delete_share_object,
    get_share_object,
)
from integration_tests.modules.shares.utils import check_share_ready

REDSHIFT_PRINCIPAL_TYPE = 'RedshiftRole'  # Value from backend Enum
REDSHIFT_ITEM_TYPE = 'RedshiftTable'  # Value from backend Enum
REDSHIFT_TEST_ROLE_NAME = 'testrole'  # Created following instructions in README

log = logging.getLogger(__name__)

"""
Tests cover 2 scenarios:
1. Cross account share from serverless cluster to provisioned cluster
2. Cross account share from provisioned cluster to serverless cluster
We have picked the most complex cases that should encapsulate the simpler ones (same account shares).

Some test cases that require extra clusters have been skipped as they are well covered in the unit tests
# def test_create_redshift_share_invalid_clusters():
# def test_create_redshift_share_invalid_source_connection():
"""


def create_and_submit_share_request(client, dataset, rs_table, group, env, principal_id):
    share = create_share_object(
        client=client,
        dataset_or_item_params={'datasetUri': dataset.datasetUri},
        environmentUri=env.environmentUri,
        groupUri=group,
        principalId=principal_id,
        principalRoleName=REDSHIFT_TEST_ROLE_NAME,
        principalType=REDSHIFT_PRINCIPAL_TYPE,
        requestPurpose='Integration tests - Redshift shares',
        attachMissingPolicies=False,
        permissions=['Read'],
    )
    share_item_uri = add_share_item(
        client=client, shareUri=share.shareUri, itemUri=rs_table.rsTableUri, itemType=REDSHIFT_ITEM_TYPE
    )
    submit_share_object(
        client=client,
        shareUri=share.shareUri,
    )
    return share, share_item_uri


@pytest.fixture(scope='module')
def submitted_redshift_share_request_source_serverless(
    client5,
    group5,
    session_redshift_dataset_serverless,
    session_redshift_dataset_serverless_table,
    session_connection_serverless_admin,
    session_connection_cluster_admin,
    session_cross_acc_env_1,
):
    share = None
    try:
        share, share_item_uri = create_and_submit_share_request(
            client=client5,
            dataset=session_redshift_dataset_serverless,
            rs_table=session_redshift_dataset_serverless_table,
            group=group5,
            env=session_cross_acc_env_1,
            principal_id=session_connection_cluster_admin.connectionUri,
        )
        yield share, share_item_uri
    finally:
        if share:
            share = get_share_object(client=client5, shareUri=share.shareUri)
            items_to_revoke = [
                item.shareItemUri
                for item in share['items'].nodes
                if item.status in ['Share_Succeeded', 'Revoke_Failed']
            ]
            if items_to_revoke:
                revoke_share_items(client=client5, shareUri=share.shareUri, shareItemUris=items_to_revoke)
                check_share_ready(client=client5, shareUri=share.shareUri)
            delete_share_object(client=client5, shareUri=share.shareUri)


@pytest.fixture(scope='module')
def submitted_redshift_share_request_source_cluster(
    client1,
    group1,
    session_redshift_dataset_cluster,
    session_redshift_dataset_cluster_table,
    session_connection_serverless_admin,
    session_connection_cluster_admin,
    session_env1,
):
    share = None
    try:
        share, share_item_uri = create_and_submit_share_request(
            client=client1,
            dataset=session_redshift_dataset_cluster,
            rs_table=session_redshift_dataset_cluster_table,
            group=group1,
            env=session_env1,
            principal_id=session_connection_serverless_admin.connectionUri,
        )
        yield share, share_item_uri
    finally:
        if share:
            share = get_share_object(client=client1, shareUri=share.shareUri)
            items_to_revoke = [
                item.shareItemUri
                for item in share['items'].nodes
                if item.status in ['Share_Succeeded', 'Revoke_Failed']
            ]
            if items_to_revoke:
                revoke_share_items(client=client1, shareUri=share.shareUri, shareItemUris=items_to_revoke)
                check_share_ready(client=client1, shareUri=share.shareUri)
            delete_share_object(client=client1, shareUri=share.shareUri)
