import logging
import time
from assertpy import assert_that

import re
from integration_tests.utils import poller

from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_in_progress, check_stack_ready
from integration_tests.errors import GqlError
from tests_new.integration_tests.modules.notebooks.queries import (
    get_sagemaker_notebook,
    list_sagemaker_notebooks,
    start_sagemaker_notebook,
    stop_sagemaker_notebook,
)

log = logging.getLogger(__name__)


def is_notebook_ready(notebook):
    return re.match(r'Stopping|Pending|Deleting|Updating', notebook.NotebookInstanceStatus, re.IGNORECASE)


@poller(check_success=lambda notebook: not is_notebook_ready(notebook), timeout=600)
def check_notebook_ready(client, notebook_uri):
    return get_sagemaker_notebook(client, notebook_uri)


def test_create_notebook(session_notebook1):
    assert_that(session_notebook1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_list_notebooks_authorized(client1, session_notebook1, session_id):
    assert_that(list_sagemaker_notebooks(client1, term=session_id).nodes).is_length(1)


def test_list_notebooks_unauthorized(client2, session_notebook1, session_id):
    assert_that(list_sagemaker_notebooks(client2, term=session_id).nodes).is_length(0)


def test_stop_notebook_unauthorized(client1, client2, session_notebook1):
    assert_that(stop_sagemaker_notebook).raises(GqlError).when_called_with(
        client2, session_notebook1.notebookUri
    ).contains('UnauthorizedOperation', session_notebook1.notebookUri)
    notebook = get_sagemaker_notebook(client1, session_notebook1.notebookUri)
    assert_that(notebook.NotebookInstanceStatus).is_equal_to('InService')


def test_stop_notebook_authorized(client1, session_notebook1):
    assert_that(stop_sagemaker_notebook(client1, notebookUri=session_notebook1.notebookUri)).is_equal_to('Stopping')
    notebook = get_sagemaker_notebook(client1, session_notebook1.notebookUri)
    assert_that(notebook.NotebookInstanceStatus).matches(r'Stopping|Stopped')
    check_notebook_ready(client1, session_notebook1.notebookUri)


def test_start_notebook_unauthorized(client1, client2, session_notebook1):
    assert_that(start_sagemaker_notebook).raises(GqlError).when_called_with(
        client2, session_notebook1.notebookUri
    ).contains('UnauthorizedOperation', session_notebook1.notebookUri)
    notebook = get_sagemaker_notebook(client1, session_notebook1.notebookUri)
    assert_that(notebook.NotebookInstanceStatus).is_equal_to('Stopped')


def test_start_notebook_authorized(client1, session_notebook1):
    assert_that(start_sagemaker_notebook(client1, notebookUri=session_notebook1.notebookUri)).is_equal_to('Starting')
    notebook = get_sagemaker_notebook(client1, session_notebook1.notebookUri)
    assert_that(notebook.NotebookInstanceStatus).matches(r'Pending|InService')
    check_notebook_ready(client1, session_notebook1.notebookUri)


def test_persistent_notebook_update(client1, persistent_notebook1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_notebook1.stack.stackUri
    env_uri = persistent_notebook1.environment.environmentUri
    notebook_uri = persistent_notebook1.notebookUri
    target_type = 'notebook'
    check_stack_ready(
        client=client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=notebook_uri, target_type=target_type
    )
    update_stack(client1, notebook_uri, target_type)
    # wait for stack to move to "in_progress" state
    # TODO: Come up with better way to handle wait in progress if applicable
    # Use time.sleep() instead of poller b/c of case where no changes founds  (i.e. no update required)
    # check_stack_in_progress(client1, env_uri, stack_uri)
    time.sleep(120)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=notebook_uri, target_type=target_type
    )
    assert_that(stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')
