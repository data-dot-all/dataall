import logging
from datetime import datetime
import time
from assertpy import assert_that

from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_in_progress, check_stack_ready
from integration_tests.errors import GqlError
from tests_new.integration_tests.modules.notebooks.queries import list_sagemaker_notebooks

log = logging.getLogger(__name__)


def test_create_notebook(session_env1):
    assert_that(session_env1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_list_envs_authorized(client1, session_notebook1, session_id):
    assert_that(list_sagemaker_notebooks(client1, term=session_id).nodes).is_length(1)


def test_list_envs_unauthorized(client2, session_notebook1, session_id):
    assert_that(list_sagemaker_notebooks(client2, term=session_id).nodes).is_length(0)


def test_persistent_notebook_update(client1, persistent_notebook1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_notebook1.stack.stackUri
    env_uri = persistent_notebook1.environmentUri
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
    time.sleep(10)

    stack = check_stack_ready(
        client1, env_uri=env_uri, stack_uri=stack_uri, target_uri=notebook_uri, target_type=target_type
    )
    assert_that(stack.status).is_equal_to('UPDATE_COMPLETE')

