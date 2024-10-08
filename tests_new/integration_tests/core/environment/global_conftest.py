import logging

import pytest
import boto3

from integration_tests.aws_clients.sts import STSClient
from integration_tests.client import GqlError
from integration_tests.core.environment.queries import (
    create_environment,
    get_environment,
    delete_environment,
    list_environments,
    invite_group_on_env,
)
from integration_tests.core.organizations.queries import create_organization
from integration_tests.core.stack.utils import check_stack_ready
from tests_new.integration_tests.core.environment.utils import update_env_stack
from tests_new.integration_tests.aws_clients.s3 import S3Client

log = logging.getLogger(__name__)


def create_env(client, env_name, group, org_uri, account_id, region, tags=[]):
    env = create_environment(
        client, name=env_name, group=group, organizationUri=org_uri, awsAccountId=account_id, region=region, tags=tags
    )
    check_stack_ready(client, env.environmentUri, env.stack.stackUri)
    return get_environment(client, env.environmentUri)


def delete_env(client, env):
    check_stack_ready(client, env.environmentUri, env.stack.stackUri)
    try:
        return delete_environment(client, env.environmentUri)
    except GqlError:
        log.exception('unexpected error when deleting environment')
        return False


"""
Session envs persist accross the duration of the whole integ test suite and are meant to make the test suite run faster (env creation takes ~2 mins).
For this reason they must stay immutable as changes to them will affect the rest of the tests.
"""


@pytest.fixture(scope='session')
def session_env1(client1, group1, org1, session_id, testdata):
    envdata = testdata.envs['session_env1']
    env = None
    try:
        env = create_env(
            client1, 'session_env1', group1, org1.organizationUri, envdata.accountId, envdata.region, tags=[session_id]
        )
        yield env
    finally:
        if env:
            role = f'arn:aws:iam::{env.AwsAccountId}:role/dataall-integration-tests-role-{env.region}'
            session = get_environment_aws_session(role, env)
            S3Client(session=session, account=env.AwsAccountId, region=env.region).delete_bucket(
                env.EnvironmentDefaultBucketName
            )
            delete_env(client1, env)


@pytest.fixture(scope='session')
def session_env1_integration_role_arn(session_env1):
    return f'arn:aws:iam::{session_env1.AwsAccountId}:role/dataall-integration-tests-role-{session_env1.region}'


@pytest.fixture(scope='session')
def session_env1_aws_client(session_env1, session_env1_integration_role_arn):
    return STSClient(
        role_arn=session_env1_integration_role_arn, region=session_env1.get('region'), session_name='Session_1'
    ).get_refreshable_session()


@pytest.fixture(scope='session')
def session_cross_acc_env_1(client5, group5, testdata, org1, session_id):
    envdata = testdata.envs['session_cross_acc_env_1']
    env = None
    try:
        env = create_env(
            client5,
            'session_cross_acc_env_1',
            group5,
            org1.organizationUri,
            envdata.accountId,
            envdata.region,
            tags=[session_id],
        )
        yield env
    finally:
        if env:
            delete_env(client5, env)


@pytest.fixture(scope='session')
def session_cross_acc_env_1_integration_role_arn(session_cross_acc_env_1):
    return f'arn:aws:iam::{session_cross_acc_env_1.AwsAccountId}:role/dataall-integration-tests-role-{session_cross_acc_env_1.region}'


@pytest.fixture(scope='session')
def session_cross_acc_env_1_aws_client(session_cross_acc_env_1, session_cross_acc_env_1_integration_role_arn):
    return STSClient(
        role_arn=session_cross_acc_env_1_integration_role_arn,
        region=session_cross_acc_env_1.get('region'),
        session_name='Session_cross_1',
    ).get_refreshable_session()


@pytest.fixture(scope='session')
def persistent_env1_integration_role_arn(persistent_env1):
    return f'arn:aws:iam::{persistent_env1.AwsAccountId}:role/dataall-integration-tests-role-{persistent_env1.region}'


@pytest.fixture(scope='session')
def persistent_env1_aws_client(persistent_env1, persistent_env1_integration_role_arn):
    return STSClient(
        role_arn=persistent_env1_integration_role_arn, region=persistent_env1.get('region'), session_name='Persistent_1'
    ).get_refreshable_session()


@pytest.fixture(scope='session')
def session_env2(client1, group1, group2, org2, session_id, testdata):
    envdata = testdata.envs['session_env2']
    env = None
    try:
        env = create_env(
            client1, 'session_env2', group1, org2.organizationUri, envdata.accountId, envdata.region, tags=[session_id]
        )
        invite_group_on_env(client1, env.environmentUri, group2, ['CREATE_DATASET'])
        yield env
    finally:
        if env:
            delete_env(client1, env)


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_env1(client1, group1, org1, testdata):
    envdata = testdata.envs['temp_env1']
    env = None
    try:
        env = create_env(client1, 'temp_env1', group1, org1.organizationUri, envdata.accountId, envdata.region)
        yield env
    finally:
        if env:
            delete_env(client1, env)


"""
Persistent environments must always be present (if not i.e first run they will be created but won't be removed).
They are suitable for testing backwards compatibility. 
"""


def get_or_create_persistent_env(env_name, client, group, testdata):
    envs = list_environments(client, term=env_name).nodes
    if envs:
        return envs[0]
    else:
        envdata = testdata.envs[env_name]
        org = create_organization(client, f'org_{env_name}', group)
        env = create_env(
            client, env_name, group, org.organizationUri, envdata.accountId, envdata.region, tags=[env_name]
        )
        if env.stack.status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return env
        else:
            delete_env(client, env)
            raise RuntimeError(f'failed to create {env_name=} {env=}')


@pytest.fixture(scope='session')
def persistent_env1(client1, group1, testdata):
    return get_or_create_persistent_env('persistent_env1', client1, group1, testdata)


@pytest.fixture(scope='session')
def updated_persistent_env1(client1, group1, persistent_env1):
    update_env_stack(client1, persistent_env1)
    return get_environment(client1, persistent_env1.environmentUri)


@pytest.fixture(scope='session')
def persistent_cross_acc_env_1(client5, group5, testdata):
    return get_or_create_persistent_env('persistent_cross_acc_env_1', client5, group5, testdata)


@pytest.fixture(scope='session')
def updated_persistent_cross_acc_env_1(client5, group5, persistent_cross_acc_env_1):
    update_env_stack(client5, persistent_cross_acc_env_1)
    return get_environment(client5, persistent_cross_acc_env_1.environmentUri)


@pytest.fixture(scope='session')
def persistent_cross_acc_env_1_integration_role_arn(persistent_cross_acc_env_1):
    return f'arn:aws:iam::{persistent_cross_acc_env_1.AwsAccountId}:role/dataall-integration-tests-role-{persistent_cross_acc_env_1.region}'


@pytest.fixture(scope='session')
def persistent_cross_acc_env_1_aws_client(persistent_cross_acc_env_1, persistent_cross_acc_env_1_integration_role_arn):
    return STSClient(
        role_arn=persistent_cross_acc_env_1_integration_role_arn,
        region=persistent_cross_acc_env_1.get('region'),
        session_name='Persistent_cross_1',
    ).get_refreshable_session()
