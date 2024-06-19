from assertpy import assert_that

from integration_tests.core.environment.queries import update_environment, get_environment
from integration_tests.errors import GqlError


def test_create_env(session_env1):
    assert_that(session_env1.stack.status).is_equal_to('CREATE_COMPLETE')


def test_modify_env(client1, session_env1):
    test_description = 'a test description'
    env_uri = session_env1.environmentUri
    update_environment(client1, env_uri, {'description': test_description})
    env = get_environment(client1, env_uri)
    assert_that(env.description).is_equal_to(test_description)


def test_modify_env_unauthorized(client2, session_env1):
    test_description = 'unauthorized'
    env_uri = session_env1.environmentUri
    assert_that(update_environment).raises(GqlError).when_called_with(
        client2, env_uri, {'description': test_description}
    ).contains(
        'UnauthorizedOperation',
        env_uri,
    )
