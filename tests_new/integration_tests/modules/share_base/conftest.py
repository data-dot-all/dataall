import json

import boto3
import pytest

from tests_new.integration_tests.aws_clients.iam import IAMClient
from tests_new.integration_tests.core.environment.queries import add_consumption_role, remove_consumption_role
from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.modules.s3_datasets.aws_clients import GlueClient
from tests_new.integration_tests.modules.s3_datasets.global_conftest import get_or_create_persistent_s3_dataset
from tests_new.integration_tests.modules.s3_datasets.queries import create_folder, generate_dataset_access_token, \
    sync_tables
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    delete_share_object,
    get_share_object,
    revoke_share_items,
)
from tests_new.integration_tests.modules.share_base.utils import check_share_ready
from dataall.modules.shares_base.services.shares_enums import ShareItemStatus

test_cons_role_name = 'ShareTestConsumptionRole'


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
def persistent_s3_dataset_for_share_test(client1, group1, persistent_env1, testdata):
    dataset = get_or_create_persistent_s3_dataset('persistent_s3_dataset_for_share_test', client1, group1,
                                                  persistent_env1)

    try:
        create_folder(
            client1,
            dataset.datasetUri,
            {
                'label': 'folder1',
                'prefix': 'folder1'
            }
        )
        creds = json.loads(generate_dataset_access_token(client1, dataset.datasetUri))
        print(creds)
        dataset_session = boto3.Session(
            aws_access_key_id=creds['AccessKey'],
            aws_secret_access_key=creds['SessionKey'],
            aws_session_token=creds['sessionToken'],
        )
        GlueClient(dataset_session, dataset.region).create_table(
            database_name=dataset.GlueDatabaseName, table_name='integrationtest', bucket=dataset.S3BucketName
        )
        response = sync_tables(client1, datasetUri=dataset.datasetUri)
    except Exception as e:
        print(e)

    return dataset


@pytest.fixture(scope='session')
def persistent_s3_dataset_for_share_test_autoapproval(client1, group1, persistent_env1, testdata):
    dataset = get_or_create_persistent_s3_dataset('persistent_s3_dataset_autoapproval', client1, group1,
                                                  persistent_env1, autoApprovalEnabled=True)

    return dataset

@pytest.fixture(scope='session')
def consumption_role_1(client5, group5, persistent_env1):
    iam_client = IAMClient(session=None, region=persistent_env1['region'])
    iam_client.create_role_if_not_exists(persistent_env1.AwsAccountId, test_cons_role_name)
    consumption_role = add_consumption_role(
        client5, persistent_env1.environmentUri, group5, 'ShareTestConsumptionRole',
        f'arn:aws:iam::{persistent_env1.AwsAccountId}:role/{test_cons_role_name}'
    )
    yield consumption_role
    remove_consumption_role(client5, persistent_env1.environmentUri, consumption_role.consumptionRoleUri)


@pytest.fixture(scope='session')
def session_share_1(client5, client1, persistent_env1, persistent_s3_dataset_for_share_test, group5):
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


@pytest.fixture(scope='session')
def session_share_consrole_1(client5, client1, persistent_env1, persistent_s3_dataset_for_share_test, group5, consumption_role_1):
    share1cr = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_s3_dataset_for_share_test.datasetUri},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share1cr = get_share_object(client5, share1cr.shareUri)
    yield share1cr
    clean_up_share(client5, share1cr.shareUri)


@pytest.fixture(scope='session')
def session_share_consrole_2(client5, client1, persistent_env1, persistent_s3_dataset_for_share_test_autoapproval, group5, consumption_role_1):
    share2cr = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': persistent_s3_dataset_for_share_test_autoapproval.datasetUri},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group5,
        principalId=consumption_role_1.consumptionRoleUri,
        principalType=PrincipalType.ConsumptionRole.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share2cr = get_share_object(client5, share2cr.shareUri)
    yield share2cr

    clean_up_share(client5, share2cr.shareUri)

