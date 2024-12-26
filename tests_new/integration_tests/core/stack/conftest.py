import pytest

from integration_tests.core.stack.queries import update_key_value_tags


@pytest.fixture(scope='function')
def environment_tags_1(client1, session_env1, session_id):
    tags = None
    try:
        tags = update_key_value_tags(
            client1,
            input={
                'targetUri': session_env1.environmentUri,
                'targetType': 'environment',
                'tags': [
                    {'key': 'key1', 'value': session_id, 'cascade': False},
                    {'key': 'key2', 'value': session_id, 'cascade': True},
                ],
            },
        )
        yield tags
    finally:
        if tags:
            update_key_value_tags(
                client1,
                input={
                    'targetUri': session_env1.environmentUri,
                    'targetType': 'environment',
                    'tags': [],
                },
            )
