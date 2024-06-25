from datetime import datetime

from assertpy import assert_that

from integration_tests.core.environment.queries import update_environment, get_environment
from integration_tests.errors import GqlError


def test_create_env(session_env1):
    assert_that(session_env1.stack.status).is_equal_to('CREATE_COMPLETE')


def test_modify_env(client1, session_env1):
    test_description = f'a test description {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    updated_env = update_environment(client1, env_uri, {'description': test_description})
    assert_that(updated_env).contains_entry({'environmentUri': env_uri}, {'description': test_description})
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry({'environmentUri': env_uri}, {'description': test_description})


def test_modify_env_unauthorized(client1, client2, session_env1):
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    assert_that(update_environment).raises(GqlError).when_called_with(
        client2, env_uri, {'description': test_description}
    ).contains('UnauthorizedOperation', env_uri)
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry({'environmentUri': env_uri}).does_not_contain_entry(
        {'description': test_description}
    )
