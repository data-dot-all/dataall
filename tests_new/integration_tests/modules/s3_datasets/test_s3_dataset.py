import logging
import os
import json
from datetime import datetime
import time
from assertpy import assert_that
import requests
import pytest

from integration_tests.modules.s3_datasets.queries import (
    delete_dataset,
    get_dataset,
    get_dataset_assume_role_url,
    generate_dataset_access_token,
    get_dataset_presigned_role_url,
    start_glue_crawler,
    update_dataset,
)
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_ready
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)

@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
# Dataset Mutations
def test_create_import_s3_dataset(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    assert_that(dataset.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_create_s3_dataset_unauthorized(client2, session_env1):
    pass #TODO

@pytest.mark.parametrize(
    'dataset_fixture_name,label',
    [
        ('session_s3_dataset1', 'TestDatasetCreated'),
        ('session_imported_sse_s3_dataset1', 'TestDatasetImported'),
        ('session_imported_kms_s3_dataset1', 'TestDatasetImported'),
    ],
)
def test_get_s3_dataset(client1, dataset_fixture_name, label, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    response = get_dataset(client1, dataset.datasetUri)
    assert_that(response.label).is_equal_to(label)


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_s3_dataset_non_admin(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    assert_that(dataset.userRoleForDataset).is_equal_to('NoPermission')


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_dataset_assume_role_url(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    assert_that(get_dataset_assume_role_url(client1, dataset.datasetUri)).starts_with(
        'https://signin.aws.amazon.com/federation'
    )

@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_dataset_assume_role_url_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(get_dataset_assume_role_url).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
    )

@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_dataset_presigned_url_upload_data(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    file_path = os.path.join(os.path.dirname(__file__), 'sample_data/csv_table/csv_sample.csv')
    prefix = 'csv_table'
    file_name = 'csv_sample.csv'

    response = json.loads(
        get_dataset_presigned_role_url(client1, dataset_uri, input={'prefix': prefix, 'fileName': file_name})
    )
    assert_that(response).contains_key('url', 'fields')
    with open(file_path, 'rb') as f:
        # Create a dictionary with the form fields and the file data
        files = {'file': (f'{prefix}/{file_name}', f)}

        # Send the POST request with the presigned URL, form fields, and file data
        http_response = requests.post(response['url'], data=response['fields'], files=files)
        http_response.raise_for_status()

@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_get_dataset_presigned_url_upload_data_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(get_dataset_presigned_role_url).raises(GqlError).when_called_with(
        client2, dataset_uri, input={'prefix': 'sample_data', 'fileName': 'name'}
    ).contains('UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri)


def test_list_s3_datasets_owned_by_env_group():
    # TODO
    pass


def test_list_s3_datasets_owned_by_env_group_unauthorized():
    # TODO
    pass


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_update_dataset(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    test_description = f'a test description {datetime.utcnow().isoformat()}'
    dataset_uri = dataset.datasetUri
    updated_dataset = update_dataset(
        client1, dataset_uri, {'description': test_description, 'KmsAlias': dataset.KmsAlias}
    )
    assert_that(updated_dataset).contains_entry(datasetUri=dataset_uri, description=test_description)
    env = get_dataset(client1, dataset_uri)
    assert_that(env).contains_entry(datasetUri=dataset_uri, description=test_description)


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1', 'session_imported_sse_s3_dataset1', 'session_imported_kms_s3_dataset1'],
)
def test_update_dataset_unauthorized(client1, client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    dataset_uri = dataset.datasetUri
    assert_that(update_dataset).raises(GqlError).when_called_with(
        client2, dataset_uri, {'description': test_description, 'KmsAlias': dataset.KmsAlias}
    ).contains('UnauthorizedOperation', dataset_uri)
    response = get_dataset(client1, dataset_uri)
    assert_that(response).contains_entry(datasetUri=dataset_uri).does_not_contain_entry(description=test_description)


def test_delete_s3_dataset():
    # TODO
    pass


def test_delete_dataset_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(delete_dataset).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', dataset_uri
    )


def test_generate_dataset_access_token(client1, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    creds = generate_dataset_access_token(client1, dataset_uri)
    assert_that(json.loads(creds)).contains_key('AccessKey', 'SessionKey', 'sessionToken')


def test_generate_dataset_access_token_unauthorized(client1, client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    assert_that(generate_dataset_access_token).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
    )


def test_start_crawler(client1, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    response = start_glue_crawler(client1, datasetUri=dataset_uri, input=None)
    assert_that(response.get('Name')).is_equal_to(session_s3_dataset1.GlueCrawlerName)
    assert_that(response.get('status')).is_in(['Pending', 'Running'])
    # TODO: check it can run successfully + check sending prefix


def test_start_crawler_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(start_glue_crawler).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CRAWL_DATASET', dataset_uri
    )


## Backwards compatibility
def test_persistent_s3_dataset_update(client1, persistent_s3_dataset1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_s3_dataset1.stack.stackUri
    env_uri = persistent_s3_dataset1.environment.environmentUri
    dataset_uri = persistent_s3_dataset1.datasetUri
    target_type = 'dataset'
    check_stack_ready(
        client=client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type
    )
    update_stack(client1, dataset_uri, target_type)
    # wait for stack to move to "in_progress" state

    # TODO: Come up with better way to handle wait in progress if applicable
    # Use time.sleep() instead of poller b/c of case where no changes founds  (i.e. no update required)
    # check_stack_in_progress(client1, env_uri, stack_uri)
    time.sleep(120)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type
    )
    assert_that(stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_persistent_import_sse_s3_dataset_update(client1, persistent_imported_sse_s3_dataset1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_imported_sse_s3_dataset1.stack.stackUri
    env_uri = persistent_imported_sse_s3_dataset1.environment.environmentUri
    dataset_uri = persistent_imported_sse_s3_dataset1.datasetUri
    target_type = 'dataset'
    check_stack_ready(client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type)
    update_stack(client1, dataset_uri, target_type)
    # wait for stack to move to "in_progress" state

    # TODO: Come up with better way to handle wait in progress if applicable
    # Use time.sleep() instead of poller b/c of case where no changes founds  (i.e. no update required)
    # check_stack_in_progress(client1, env_uri, stack_uri)
    time.sleep(120)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type
    )
    assert_that(stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_persistent_import_kms_s3_dataset_update(client1, persistent_imported_kms_s3_dataset1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_imported_kms_s3_dataset1.stack.stackUri
    env_uri = persistent_imported_kms_s3_dataset1.environment.environmentUri
    dataset_uri = persistent_imported_kms_s3_dataset1.datasetUri
    target_type = 'dataset'
    check_stack_ready(client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type)
    update_stack(client1, dataset_uri, 'dataset')
    # wait for stack to move to "in_progress" state

    # TODO: Come up with better way to handle wait in progress if applicable
    # Use time.sleep() instead of poller b/c of case where no changes founds  (i.e. no update required)
    # check_stack_in_progress(client1, env_uri, stack_uri)
    time.sleep(120)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type
    )
    assert_that(stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')
