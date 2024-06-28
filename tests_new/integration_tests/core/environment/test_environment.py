import logging
from datetime import datetime

from assertpy import assert_that

from integration_tests.core.environment.queries import get_environment, update_environment, list_environments
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_in_progress, check_stack_ready
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_create_env(session_env1):
    assert_that(session_env1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_modify_env(client1, session_env1):
    test_description = f'a test description {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    updated_env = update_environment(client1, env_uri, {'description': test_description})
    assert_that(updated_env).contains_entry(environmentUri=env_uri, description=test_description)
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry(environmentUri=env_uri, description=test_description)


def test_modify_env_unauthorized(client1, client2, session_env1):
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    assert_that(update_environment).raises(GqlError).when_called_with(
        client2, env_uri, {'description': test_description}
    ).contains('UnauthorizedOperation', env_uri)
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry(environmentUri=env_uri).does_not_contain_entry(description=test_description)


def test_list_envs_authorized(client1, session_env1, session_env2, session_id):
    assert_that(list_environments(client1, term=session_id).nodes).is_length(2)


def test_list_envs_unauthorized(client2, session_env1, session_env2, session_id):
    assert_that(list_environments(client2, term=session_id).nodes).is_length(0)


def test_persistent_env_update(client1, persistent_env1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_env1.stack.stackUri
    env_uri = persistent_env1.environmentUri
    check_stack_ready(client1, env_uri, stack_uri)
    update_stack(client1, env_uri, 'environment')
    # wait for stack to move to "in_progress" state
    check_stack_in_progress(client1, env_uri, stack_uri)
    stack = check_stack_ready(client1, env_uri, stack_uri)
    assert_that(stack.status).is_equal_to('UPDATE_COMPLETE')
