import logging
import os
import json
from datetime import datetime
import time
from assertpy import assert_that
import requests

from integration_tests.modules.s3_datasets.queries import (
    create_folder,
    delete_dataset,
    delete_folder,
    delete_table,
    get_dataset,
    get_dataset_assume_role_url,
    generate_dataset_access_token,
    get_dataset_presigned_role_url,
    preview_table,
    start_dataset_profiling_run,
    start_glue_crawler,
    sync_tables,
    update_dataset,
)
from integration_tests.modules.datasets_base.queries import list_datasets
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_ready
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


def test_get_s3_dataset_non_admin(client2, session_s3_dataset1):
    dataset = get_dataset(client2, session_s3_dataset1.datasetUri)
    assert dataset
    assert_that(dataset.userRoleForDataset).is_equal_to('NoPermission')


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
    updated_dataset = update_dataset(
        client1, dataset_uri, {'description': test_description, 'KmsAlias': session_s3_dataset1.KmsAlias}
    )
    assert_that(updated_dataset).contains_entry(datasetUri=dataset_uri, description=test_description)
    env = get_dataset(client1, dataset_uri)
    assert_that(env).contains_entry(datasetUri=dataset_uri, description=test_description)


def test_modify_dataset_unauthorized(client1, client2, session_s3_dataset1):
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(update_dataset).raises(GqlError).when_called_with(
        client2, dataset_uri, {'description': test_description, 'KmsAlias': session_s3_dataset1.KmsAlias}
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


def test_access_dataset_assume_role_url(client1, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    assert_that(get_dataset_assume_role_url(client1, dataset_uri)).starts_with(
        'https://signin.aws.amazon.com/federation'
    )


def test_access_dataset_assume_role_url_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri

    assert_that(get_dataset_assume_role_url).raises(GqlError).when_called_with(client2, dataset_uri).contains(
        'UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri
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


def test_get_dataset_presigned_url_upload_data(client1, session_s3_dataset1):
    # TODO: Test + Iterate for Multiple Files
    dataset_uri = session_s3_dataset1.datasetUri
    file_path = os.path.join(os.path.dirname(__file__), 'sample_data/csv_table/books.csv')
    prefix = 'csv_table'
    file_name = 'books.csv'

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


def test_get_dataset_presigned_url_upload_data_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(get_dataset_presigned_role_url).raises(GqlError).when_called_with(
        client2, dataset_uri, input={'prefix': 'sample_data', 'fileName': 'name'}
    ).contains('UnauthorizedOperation', 'CREDENTIALS_DATASET', dataset_uri)


#
#
# def test_start_crawler(client1, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     response = start_glue_crawler(client1, datasetUri=dataset_uri, input=None)
#     assert_that(response.get('Name')).is_equal_to(session_s3_dataset1.GlueCrawlerName)
#     assert_that(response.get('status')).is_in(['Pending', 'Running'])
#     # TODO: check it can run successfully + check sending prefix
#
#
# def test_start_crawler_unauthorized(client2, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     assert_that(start_glue_crawler).raises(GqlError).when_called_with(client2, dataset_uri).contains(
#         'UnauthorizedOperation', 'CRAWL_DATASET', dataset_uri
#     )
#
#
# def test_sync_tables(client1, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     response = sync_tables(client1, datasetUri=dataset_uri)
#     assert_that(response.count).is_equal_to(2)
#
#
# def test_sync_tables_unauthorized(client2, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     assert_that(sync_tables).raises(GqlError).when_called_with(client2, dataset_uri).contains(
#         'UnauthorizedOperation', 'SYNC_DATASET', dataset_uri
#     )
#
#
# def test_start_table_profiling(client1, session_s3_dataset2_with_table):
#     dataset, table = session_s3_dataset2_with_table
#     table_uri = table.tableUri
#     dataset_uri = dataset.datasetUri
#     response = start_dataset_profiling_run(
#         client1, input={'datasetUri': dataset_uri, 'tableUri': table_uri, 'GlueTableName': table.GlueTableName}
#     )
#     assert_that(response.datasetUri).is_equal_to(dataset_uri)
#     assert_that(response.status).is_equal_to('RUNNING')
#     assert_that(response.GlueTableName).is_equal_to(table.GlueTableName)
#
#
# def test_start_table_profiling_unauthorized(client2, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     assert_that(start_dataset_profiling_run).raises(GqlError).when_called_with(client2, dataset_uri).contains(
#         'UnauthorizedOperation', 'PROFILE_DATASET_TABLE', dataset_uri
#     )
#
#
# def test_preview_table(client1, session_s3_dataset2_with_table):
#     dataset, table = session_s3_dataset2_with_table
#     table_uri = table.tableUri
#     response = preview_table(client1, table_uri)
#     assert_that(response.rows).exists()
#
#
# def test_preview_table_unauthorized(client2, session_s3_dataset2_with_table):
#     dataset, table = session_s3_dataset2_with_table
#     table_uri = table.tableUri
#     # TODO: confidentiality levels
#     assert_that(preview_table).raises(GqlError).when_called_with(client2, table_uri, {}).contains(
#         'UnauthorizedOperation', 'PREVIEW_DATASET_TABLE', table_uri
#     )
#
#
# def test_delete_table(client1, session_s3_dataset2_with_table):
#     dataset, table = session_s3_dataset2_with_table
#     # todo
#
#
# def test_delete_table_unauthorized(client2, session_s3_dataset2_with_table):
#     dataset, table = session_s3_dataset2_with_table
#     table_uri = table.tableUri
#     assert_that(delete_table).raises(GqlError).when_called_with(client2, table_uri).contains(
#         'UnauthorizedOperation', 'DELETE_DATASET_TABLE', table_uri
#     )
#
#
# def test_create_folder(client1, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     response = create_folder(
#         client1, datasetUri=dataset_uri, input={'prefix': 'folderCreatedInTest', 'label': 'labelFolder'}
#     )
#     assert_that(response.S3Prefix).is_equal_to('folderCreatedInTest')
#     assert_that(response.label).is_equal_to('labelFolder')
#
#
# def test_create_folder_unauthorized(client2, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     assert_that(create_folder).raises(GqlError).when_called_with(client2, dataset_uri, {}).contains(
#         'UnauthorizedOperation', 'CREATE_DATASET_FOLDER', dataset_uri
#     )
#
#
# def test_delete_folder(client1, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     location = create_folder(
#         client1, datasetUri=dataset_uri, input={'prefix': 'folderToDelete', 'label': 'folderToDelete'}
#     )
#     response = delete_folder(client1, location.locationUri)
#     assert_that(response).is_equal_to(True)
#
#
# def test_delete_folder_unauthorized(client1, client2, session_s3_dataset1):
#     dataset_uri = session_s3_dataset1.datasetUri
#     location = create_folder(
#         client1, datasetUri=dataset_uri, input={'prefix': 'folderToDelete', 'label': 'folderToDelete'}
#     )
#     assert_that(delete_folder).raises(GqlError).when_called_with(client2, location.locationUri).contains(
#         'UnauthorizedOperation', 'DELETE_DATASET_FOLDER', location.locationUri
#     )
