from assertpy import assert_that

from integration_tests.core.stack.queries import get_stack_logs, list_key_value_tags, update_key_value_tags
from integration_tests.errors import GqlError


##  test_update_stack and test_get_stack are not needed as they are
##  tested in each module that uses stacks (e.g. integration_tests.core.environment.test_environment.test_persistent_env_update)


def test_get_env_stack_logs(client1, session_env1):
    response = get_stack_logs(client1, target_uri=session_env1.environmentUri, target_type='environment')
    assert_that(response).is_not_empty()


def test_get_env_stack_logs_unauthorized(client2, session_env1):
    assert_that(get_stack_logs).raises(GqlError).when_called_with(
        client=client2,
        target_uri=session_env1.environmentUri,
        target_type='environment',
    ).contains(
        'UnauthorizedOperation',
        'GET_ENVIRONMENT',
        session_env1.environmentUri,
    )


def test_update_key_value_tags_add_tags(client1, environment_tags_1, session_id):
    assert_that(len(environment_tags_1)).is_equal_to(2)
    assert_that(environment_tags_1[0]).contains_entry(key='key1', value=session_id, cascade=False)
    assert_that(environment_tags_1[1]).contains_entry(key='key2', value=session_id, cascade=True)


def test_update_key_value_tags_unauthorized(client2, session_env1, session_id):
    assert_that(update_key_value_tags).raises(GqlError).when_called_with(
        client=client2,
        input={
            'targetUri': session_env1.environmentUri,
            'targetType': 'environment',
            'tags': [
                {'key': 'key1U', 'value': session_id, 'cascade': False},
                {'key': 'key2U', 'value': session_id, 'cascade': True},
            ],
        },
    ).contains(
        'UnauthorizedOperation',
        'UPDATE_ENVIRONMENT',
        session_env1.environmentUri,
    )


def test_update_list_key_value_tags_add_tag_invalid_input(client1, session_env1, session_id):
    assert_that(update_key_value_tags).raises(GqlError).when_called_with(
        client=client1,
        input={
            'targetUri': session_env1.environmentUri,
            'targetType': 'environment',
            'tags': [
                {'key': 'keyDuplicated', 'value': session_id, 'cascade': False},
                {'key': 'keyDuplicated', 'value': session_id, 'cascade': True},
            ],
        },
    ).contains(
        'UnauthorizedOperation',
        'SAVE_KEY_VALUE_TAGS',
        'Duplicate tag keys found',
    )


def test_update_key_value_tags_delete_tags(client1, session_env1, session_id):
    response = update_key_value_tags(
        client1,
        input={
            'targetUri': session_env1.environmentUri,
            'targetType': 'environment',
            'tags': [
                {'key': 'key1delete', 'value': session_id, 'cascade': False},
                {'key': 'key2delete', 'value': session_id, 'cascade': True},
            ],
        },
    )
    assert_that(len(response)).is_equal_to(2)
    # Test delete tag
    response = update_key_value_tags(
        client1,
        input={
            'targetUri': session_env1.environmentUri,
            'targetType': 'environment',
            'tags': [],
        },
    )
    assert_that(response).is_equal_to([])
    # Test list tags after delete
    response = list_key_value_tags(client1, target_uri=session_env1.environmentUri, target_type='environment')
    assert_that(response).is_equal_to([])


def test_list_key_value_tags(client1, environment_tags_1, session_env1, session_id):
    response = list_key_value_tags(client1, target_uri=session_env1.environmentUri, target_type='environment')
    assert_that(len(response)).is_equal_to(2)
    assert_that(response[0]).contains_entry(key='key1', value=session_id, cascade=False)
    assert_that(response[1]).contains_entry(key='key2', value=session_id, cascade=True)
