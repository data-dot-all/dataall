import pytest

from integration_tests.core.environment.utils import set_env_params
from integration_tests.core.stack.utils import check_stack_ready
from integration_tests.modules.mlstudio.mutations import create_smstudio_user, delete_smstudio_user
from integration_tests.modules.mlstudio.queries import get_smstudio_user


@pytest.fixture(scope='session')
def smstudio_user1(session_id, client1, persistent_env1):
    set_env_params(client1, persistent_env1, mlStudiosEnabled='true')
    env_uri = persistent_env1.environmentUri
    smstudio = create_smstudio_user(
        client1,
        environmentUri=env_uri,
        groupName=persistent_env1.SamlGroupName,
        label=session_id,
    )
    smstudio_uri = smstudio.sagemakerStudioUserUri
    check_stack_ready(client1, env_uri, smstudio.stack.stackUri, smstudio_uri, 'mlstudio')
    yield get_smstudio_user(client1, smstudio_uri)
    delete_smstudio_user(client1, smstudio_uri)
