import pytest
import logging
from contextlib import contextmanager

from assertpy import assert_that

from integration_tests.aws_clients.sts import STSClient
from integration_tests.client import GqlError
from integration_tests.core.environment.queries import (
    create_environment,
    get_environment,
    delete_environment,
    list_environments,
    invite_group_on_env,
)
from integration_tests.core.organizations.queries import (
    create_organization,
    list_organizations,
    invite_team_to_organization,
)
from integration_tests.core.stack.utils import check_stack_ready
from tests_new.integration_tests.aws_clients.s3 import S3Client
from tests_new.integration_tests.core.environment.utils import update_env_stack

log = logging.getLogger(__name__)


@contextmanager
def create_env(client, env_name, group, org_uri, account_id, region, tags=[], retain=False):
    env = None
    errors = False
    try:
        env = create_environment(
            client,
            name=env_name,
            group=group,
            organizationUri=org_uri,
            awsAccountId=account_id,
            region=region,
            tags=tags,
        )
        check_stack_ready(client, env.environmentUri, env.stack.stackUri)
        env = get_environment(client, env.environmentUri)
        assert_that(env.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')
        yield env
    except Exception as e:
        errors = True
        raise e
    finally:
        if env and (not retain or errors):
            role = f'arn:aws:iam::{env.AwsAccountId}:role/dataall-integration-tests-role-{env.region}'
            session = STSClient(role_arn=role, region=env.region, session_name='Session_1').get_refreshable_session()
            S3Client(session=session, account=env.AwsAccountId, region=env.region).delete_bucket(
                env.EnvironmentDefaultBucketName
            )
            S3Client(session=session, account=env.AwsAccountId, region=env.region).delete_bucket(
                env.EnvironmentLogsBucketName
            )
            delete_env(client, env)


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
def session_env1(client1, group1, group5, org1, session_id, testdata):
    envdata = testdata.envs['session_env1']
    with create_env(
        client1, 'session_env1', group1, org1.organizationUri, envdata.accountId, envdata.region, tags=[session_id]
    ) as env:
        invite_group_on_env(client1, env.environmentUri, group5, ['CREATE_DATASET', 'CREATE_SHARE_OBJECT'])
        yield env


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
    with create_env(
        client5,
        'session_cross_acc_env_1',
        group5,
        org1.organizationUri,
        envdata.accountId,
        envdata.region,
        tags=[session_id],
    ) as env:
        yield env


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
    with create_env(
        client1, 'session_env2', group1, org2.organizationUri, envdata.accountId, envdata.region, tags=[session_id]
    ) as env:
        invite_group_on_env(client1, env.environmentUri, group2, ['CREATE_DATASET'])
        yield env


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_env1(client1, group1, org1, testdata):
    envdata = testdata.envs['temp_env1']
    with create_env(client1, 'temp_env1', group1, org1.organizationUri, envdata.accountId, envdata.region) as env:
        yield env


"""
Persistent environments must always be present (if not i.e first run they will be created but won't be removed).
They are suitable for testing backwards compatibility. 
"""


@contextmanager
def get_or_create_persistent_env(env_name, client, group, testdata):
    envs = list_environments(client, term=env_name).nodes
    if envs:
        env = envs[0]
        update_env_stack(client, env)
        yield get_environment(client, env.environmentUri)
    else:
        envdata = testdata.envs[env_name]
        org = create_organization(client, f'org_{env_name}', group)
        with create_env(
            client,
            env_name,
            group,
            org.organizationUri,
            envdata.accountId,
            envdata.region,
            tags=[env_name],
            retain=True,
        ) as env:
            yield env


@pytest.fixture(scope='session')
def persistent_env1(client1, group1, testdata):
    with get_or_create_persistent_env('persistent_env1', client1, group1, testdata) as env:
        yield env


@pytest.fixture(scope='session')
def persistent_cross_acc_env_1(client5, group5, client6, group6, testdata):
    with get_or_create_persistent_env('persistent_cross_acc_env_1', client5, group5, testdata) as env:
        orgs = [org.organizationUri for org in list_organizations(client6).nodes]
        envs = [org.environmentUri for org in list_environments(client6).nodes]
        if env.organization.organizationUri not in orgs:
            invite_team_to_organization(client5, env.organization.organizationUri, group6)
        if env.environmentUri not in envs:
            invite_group_on_env(
                client5,
                env.environmentUri,
                group6,
                [
                    'UPDATE_ENVIRONMENT',
                    'GET_ENVIRONMENT',
                    'ADD_ENVIRONMENT_CONSUMPTION_ROLES',
                    'LIST_ENVIRONMENT_CONSUMPTION_ROLES',
                    'LIST_ENVIRONMENT_GROUPS',
                    'CREDENTIALS_ENVIRONMENT',
                    'CREATE_SHARE_OBJECT',
                    'LIST_ENVIRONMENT_SHARED_WITH_OBJECTS',
                ],
            )
            update_env_stack(client5, env)
        yield env


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
