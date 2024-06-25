import logging
import re

import pytest

from integration_tests.client import GqlError
from integration_tests.core.environment.queries import create_environment, get_environment, delete_environment
from integration_tests.utils import poller

log = logging.getLogger(__name__)


@poller(check_success=lambda env: not re.match(r'.*IN_PROGRESS|PENDING', env.stack.status, re.IGNORECASE), timeout=600)
def check_env_ready(client, env_uri):
    env = get_environment(client, env_uri)
    log.info(f'polling {env_uri=}, new {env.stack.status=}')
    return env


def create_env(client, group, org_uri, account_id, region):
    new_env_uri = create_environment(
        client, name='testEnvA', group=group, organizationUri=org_uri, awsAccountId=account_id, region=region
    )['environmentUri']
    return check_env_ready(client, new_env_uri)


def delete_env(client, env_uri):
    check_env_ready(client, env_uri)
    try:
        return delete_environment(client, env_uri)
    except GqlError:
        log.exception('unexpected error when deleting environment')
        return False


"""
Session envs persist accross the duration of the whole integ test suite and are meant to make the test suite run faster (env creation takes ~2 mins).
For this reason they must stay immutable as changes to them will affect the rest of the tests.
"""


@pytest.fixture(scope='session')
def session_env1(client1, group1, org1, testdata):
    envdata = testdata.envs['session_env1']
    env = None
    try:
        env = create_env(client1, group1, org1['organizationUri'], envdata.accountId, envdata.region)
        yield env
    finally:
        if env:
            delete_env(client1, env['environmentUri'])


@pytest.fixture(scope='session')
def session_env2(client1, group1, org1, testdata):
    envdata = testdata.envs['session_env2']
    env = None
    try:
        env = create_env(client1, group1, org1['organizationUri'], envdata.accountId, envdata.region)
        yield env
    finally:
        if env:
            delete_env(client1, env['environmentUri'])


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_env1(client1, group1, org1, testdata):
    envdata = testdata.envs['temp_env1']
    env = None
    try:
        env = create_env(client1, group1, org1['organizationUri'], envdata.accountId, envdata.region)
        yield env
    finally:
        if env:
            delete_env(client1, env['environmentUri'])


"""
Persistent environments must always be present (if not i.e first run they will be created but won't be removed).
They are suitable for testing backwards compatibility. 
"""


@pytest.fixture(scope='function')
def persistent_env1(client1, group1, org1, testdata): ...  # TODO
