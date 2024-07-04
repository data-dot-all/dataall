import logging
from datetime import datetime
import time
from assertpy import assert_that
import requests

from integration_tests.modules.s3_datasets.queries import (
    get_dataset,
    update_dataset,
    delete_dataset,
    get_dataset_assume_role_url,
    generate_dataset_access_token,
    get_dataset_presigned_role_url,
)
from integration_tests.modules.s3_datasets.global_conftest import create_s3_dataset
from integration_tests.modules.datasets_base.queries import list_datasets
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_in_progress, check_stack_ready
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_create_s3_dataset(client1, session_s3_dataset1):
    assert_that(session_s3_dataset1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_import_sse_s3_dataset(session_imported_sse_s3_dataset1):
    assert_that(session_imported_sse_s3_dataset1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_import_kms_s3_dataset(session_imported_kms_s3_dataset1):
    assert_that(session_imported_kms_s3_dataset1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_get_s3_dataset(client1, session_s3_dataset1):
    dataset = get_dataset(client1, session_s3_dataset1.datasetUri)
    assert dataset
    assert_that(dataset.label).is_equal_to(session_s3_dataset1.label)


def test_get_s3_dataset_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(get_dataset).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', dataset_uri
    )


def test_list_datasets(
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_datasets_unauthorized(
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client2, term=session_id).nodes).is_length(0)


def test_modify_dataset(client1, session_s3_dataset1):
    test_description = f'a test description {datetime.utcnow().isoformat()}'
    dataset_uri = session_s3_dataset1.datasetUri
    updated_dataset = update_dataset(client1, dataset_uri, {'description': test_description})
    assert_that(updated_dataset).contains_entry(datasetUri=dataset_uri, description=test_description)
    env = get_dataset(client1, dataset_uri)
    assert_that(env).contains_entry(datasetUri=dataset_uri, description=test_description)


def test_modify_dataset_unauthorized(client1, client2, session_s3_dataset1):
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(update_dataset).raises(GqlError).when_called_with(
        client2, dataset_uri, {'description': test_description}
    ).contains('UnauthorizedOperation', dataset_uri)
    dataset = get_dataset(client1, dataset_uri)
    assert_that(dataset).contains_entry(datasetUri=dataset_uri).does_not_contain_entry(description=test_description)


def test_delete_dataset_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(delete_dataset).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', dataset_uri
    )


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
    time.sleep(10)

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
    time.sleep(10)

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
    time.sleep(10)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=dataset_uri, target_type=target_type
    )
    assert_that(stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_access_dataset_assume_role_url(client1, client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    assert_that(get_dataset_assume_role_url).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
    )

    assert_that(get_dataset_assume_role_url(client1, dataset_uri)).starts_with(
        'https://signin.aws.amazon.com/federation'
    )


def test_generate_dataset_access_token(client1, client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    assert_that(generate_dataset_access_token).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
    )

    creds = generate_dataset_access_token(client1, dataset_uri)
    assert_that(creds).contains_key('AccessKey', 'SessionKey', 'sessionToken')


def test_get_dataset_presigned_url_upload_data(client1, client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(get_dataset_presigned_role_url).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
    )

    object_name = './sample_data/books.csv'

    # Upload multiple files with post request using presigned URL

    with open(object_name, 'rb') as f:
        response = get_dataset_presigned_role_url(
            client1, dataset_uri, input={'prefix': 'sample_data', 'fileName': f.name}
        )
        assert_that(response).contains_key('url', 'fields')

        files = {'file': (object_name, f)}
        http_response = requests.post(response['url'], data=response['fields'], files=files)
        http_response.raise_for_status()


# def test_upload_data_to_new_datasets_success(path_to_config, client_mapping):
#     config = Config(path_to_config).config
#     for resource in config.get("test_resources").get("created_datasets") + config.get("test_resources").get("imported_datasets"):
#         client = client_mapping.get(resource.get("username"))
#         normalized_name = f"dataall-{resource.get('name').lower()}-{resource.get('uri')}"
#         bucket_name = resource.get("aws_infra",{}).get("bucket") if resource.get("aws_infra",{}).get("bucket") else normalized_name
#         print("Getting AWS credentials for dataset IAM role")
#         creds = client.generate_dataset_access_token(datasetUri=resource.get("uri"))
#         S3Client(creds=json.loads(creds)).upload_local_folder(bucket_name=bucket_name)

# def test_upload_data_to_new_datasets_success(path_to_config, client_mapping):
#     config = Config(path_to_config).config
#     for resource in config.get("test_resources").get("created_datasets") + config.get("test_resources").get("imported_datasets"):
#         client = client_mapping.get(resource.get("username"))
#         normalized_name = f"dataall-{resource.get('name').lower()}-{resource.get('uri')}"
#         bucket_name = resource.get("aws_infra",{}).get("bucket") if resource.get("aws_infra",{}).get("bucket") else normalized_name
#         print("Getting AWS credentials for dataset IAM role")
#         creds = client.generate_dataset_access_token(datasetUri=resource.get("uri"))
#         S3Client(creds=json.loads(creds)).upload_local_folder(bucket_name=bucket_name)
