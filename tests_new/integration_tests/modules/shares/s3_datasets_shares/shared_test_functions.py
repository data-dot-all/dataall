from assertpy import assert_that
from botocore.exceptions import ClientError
import boto3

from tests_new.integration_tests.core.environment.queries import get_environment_access_token
from tests_new.integration_tests.modules.shares.queries import (
    get_share_object,
    get_s3_consumption_data,
    verify_share_items,
    revoke_share_items,
    add_share_item,
    submit_share_object,
    approve_share_object,
    remove_share_item,
)
from tests_new.integration_tests.modules.shares.utils import (
    check_share_items_verified,
    check_share_ready,
)
from tests_new.integration_tests.aws_clients.sts import STSClient
from tests_new.integration_tests.aws_clients.athena import AthenaClient
from tests_new.integration_tests.modules.s3_datasets.aws_clients import S3Client
from tests_new.integration_tests.modules.s3_datasets.queries import get_folder

import json

ALL_S3_SHARABLE_TYPES_NAMES = [
    'Table',
    'StorageLocation',
    'S3Bucket',
]


def add_all_items_to_share(client, shareUri):
    updated_share = get_share_object(client, shareUri)
    items = updated_share['items'].nodes
    for item in items:
        assert_that(add_share_item(client, shareUri, item.itemUri, item.itemType)).is_not_none()
    updated_share = get_share_object(client, shareUri)
    items = updated_share['items'].nodes
    assert_that(items).extracting('status').contains_only('PendingApproval')


def delete_all_non_shared_items(client, shareUri):
    updated_share = get_share_object(client, shareUri)
    items = updated_share['items'].nodes
    for item in items:
        if item.status in [
            'Revoke_Succeeded',
            'PendingApproval',
            'Share_Rejected',
            'Share_Failed',
        ]:
            assert_that(remove_share_item(client, item.shareItemUri)).is_true()


def check_submit_share_object(client, shareUri, dataset):
    submit_share_object(client, shareUri)
    updated_share = get_share_object(client, shareUri)
    if dataset.autoApprovalEnabled:
        assert_that(updated_share.status).is_equal_to('Approved')
    else:
        assert_that(updated_share.status).is_equal_to('Submitted')


def check_approve_share_object(client, shareUri):
    approve_share_object(client, shareUri)
    updated_share = get_share_object(client, shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to('Approved')
    items = updated_share['items'].nodes
    assert_that(items).extracting('status').contains_only('Share_Approved')


def check_share_succeeded(client, shareUri, check_contains_all_item_types=False):
    check_share_ready(client, shareUri)
    updated_share = get_share_object(client, shareUri, {'isShared': True})
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to('Processed')
    for item in items:
        assert_that(item.status).is_equal_to('Share_Succeeded')
        assert_that(item.healthStatus).is_equal_to('Healthy')
    if check_contains_all_item_types:
        assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)


def check_verify_share_items(client, shareUri, expected_health_status=['Healthy'], expected_health_msg=[]):
    share = get_share_object(client, shareUri, {'isShared': True})
    items = share['items'].nodes
    times = [item.lastVerificationTime for item in items]
    verify_share_items(client, shareUri, [item.shareItemUri for item in items])
    check_share_items_verified(client, shareUri)
    updated_share = get_share_object(client, shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).extracting('status').contains_only('Share_Succeeded')
    assert_that(items).extracting('healthStatus').contains_only(*expected_health_status)
    assert_that(items).extracting('lastVerificationTime').does_not_contain(*times)
    if expected_health_msg:
        health_msgs = ' '.join([i.healthMessage for i in items])
        assert_that(health_msgs).contains(*expected_health_msg)


def check_table_access(
    athena_client, glue_db, table_name, workgroup, athena_workgroup_output_location, should_have_access
):
    query = 'SELECT * FROM {}.{}'.format(glue_db, table_name)
    if should_have_access:
        state = athena_client.execute_query(query, workgroup, athena_workgroup_output_location)
        assert_that(state).is_equal_to('SUCCEEDED')
    else:
        state = athena_client.execute_query(query, workgroup, athena_workgroup_output_location)
        assert_that(state).is_equal_to('FAILED')


def check_bucket_access(client, s3_client, bucket_name, should_have_access):
    if should_have_access:
        assert_that(s3_client.bucket_exists(bucket_name)).is_true()
        assert_that(s3_client.list_bucket_objects(bucket_name)).is_not_none()
    else:
        assert_that(s3_client.bucket_exists(bucket_name)).is_false()
        assert_that(s3_client.list_bucket_objects).raises(ClientError).when_called_with(bucket_name).contains(
            'AccessDenied'
        )


def check_accesspoint_access(client, s3_client, access_point_arn, item_uri, should_have_access):
    folder = get_folder(client, item_uri)
    if should_have_access:
        assert_that(s3_client.list_accesspoint_folder_objects(access_point_arn, folder.S3Prefix + '/')).is_not_none()
    else:
        assert_that(s3_client.list_accesspoint_folder_objects).raises(ClientError).when_called_with(
            access_point_arn, folder.S3Prefix + '/'
        ).contains('AccessDenied')


def check_share_items_access(
    client,
    group,
    shareUri,
    share_environment,
    consumption_role,
    env_client,
):
    share = get_share_object(client, shareUri)
    dataset = share.dataset
    principal_type = share.principal.principalType
    if principal_type == 'Group':
        credentials_str = get_environment_access_token(client, share_environment.environmentUri, group)
        credentials = json.loads(credentials_str)
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKey'],
            aws_secret_access_key=credentials['SessionKey'],
            aws_session_token=credentials['sessionToken'],
        )
    elif principal_type == 'ConsumptionRole':
        session = STSClient(
            role_arn=consumption_role.IAMRoleArn, region=dataset.region, session_name='ConsumptionRole'
        ).get_role_session(env_client)
    else:
        raise Exception('wrong principal type')

    s3_client = S3Client(session, dataset.region)
    athena_client = AthenaClient(session, dataset.region)

    consumption_data = get_s3_consumption_data(client, shareUri)
    items = share['items'].nodes

    glue_db = consumption_data.sharedGlueDatabase
    access_point_arn = (
        f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{consumption_data.s3AccessPointName}'
    )
    if principal_type == 'Group':
        workgroup = athena_client.get_work_group(share_environment.label, group)
        athena_workgroup_output_location = None
    else:
        workgroup = 'primary'
        athena_workgroup_output_location = (
            f's3://dataset-{dataset.datasetUri}-session-query-results/athenaqueries/primary/'
        )

    for item in items:
        should_have_access = item.status == 'Share_Succeeded'
        if item.itemType == 'Table':
            check_table_access(
                athena_client, glue_db, item.itemName, workgroup, athena_workgroup_output_location, should_have_access
            )
        elif item.itemType == 'S3Bucket':
            check_bucket_access(client, s3_client, item.itemName, should_have_access)
        elif item.itemType == 'StorageLocation':
            check_accesspoint_access(client, s3_client, access_point_arn, item.itemUri, should_have_access)


def revoke_and_check_all_shared_items(client, shareUri, check_contains_all_item_types=False):
    share = get_share_object(client, shareUri, {'isShared': True})
    items = share['items'].nodes

    shareItemUris = [item.shareItemUri for item in items]
    revoke_share_items(client, shareUri, shareItemUris)

    updated_share = get_share_object(client, shareUri, {'isShared': True})
    assert_that(updated_share.status).is_equal_to('Revoked')
    items = updated_share['items'].nodes

    assert_that(items).extracting('status').contains_only('Revoke_Approved')
    if check_contains_all_item_types:
        assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)


def check_all_items_revoke_job_succeeded(client, shareUri, check_contains_all_item_types=False):
    check_share_ready(client, shareUri)
    updated_share = get_share_object(client, shareUri)
    items = updated_share['items'].nodes

    assert_that(updated_share.status).is_equal_to('Processed')
    assert_that(items).extracting('status').contains_only('Revoke_Succeeded')
    if check_contains_all_item_types:
        assert_that(items).extracting('itemType').contains(*ALL_S3_SHARABLE_TYPES_NAMES)
