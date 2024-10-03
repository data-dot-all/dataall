import pytest

from integration_tests.core.environment.utils import set_env_params

@pytest.fixture(scope='session')
def omics_workflows(session_id, client1, persistent_env1):
    set_env_params(client1, persistent_env1, omicsEnabled='true')
    env_uri = persistent_env1.environmentUri

    yield env_uri