import logging
from datetime import datetime
import time
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import get_dataset, update_dataset, delete_dataset
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
