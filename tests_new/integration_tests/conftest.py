import datetime
import logging
import os
import re
import sys
from dataclasses import dataclass

import pytest
from dataclasses_json import dataclass_json

from tests_new.integration_tests.client import Client

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

pytest_plugins = [
    'integration_tests.core.organizations.global_conftest',
    'integration_tests.core.environment.global_conftest',
    'integration_tests.modules.s3_datasets.global_conftest',
    'integration_tests.modules.redshift_datasets.global_conftest',
    'integration_tests.modules.shares.s3_datasets_shares.global_conftest',
]


@dataclass_json
@dataclass
class User:
    username: str
    password: str


@dataclass_json
@dataclass
class Env:
    accountId: str
    region: str


@dataclass_json
@dataclass
class Dashboard:
    dashboardId: str


@dataclass_json
@dataclass
class RedshiftConnection:
    secret_arn: str
    namespace_id: str = None
    workgroup: str = None
    cluster_id: str = None


@dataclass_json
@dataclass
class TestData:
    users: dict[str, User]
    envs: dict[str, Env]
    dashboards: dict[str, Dashboard] = None
    redshift_connections: dict[str, RedshiftConnection] = None


@pytest.fixture(scope='session', autouse=True)
def testdata() -> TestData:
    try:
        return TestData.from_json(open('testdata.json').read())
    except Exception:
        return TestData.from_json(os.getenv('TESTDATA'))


@pytest.fixture(scope='session', autouse=True)
def userdata(testdata):
    yield testdata.users


@pytest.fixture(scope='session', autouse=True)
def userTenant(userdata):
    # Existing user with name and password
    # This user needs to belong to `DAAdministrators` group
    yield userdata['testUserTenant']


@pytest.fixture(scope='session', autouse=True)
def user1(userdata):
    # Existing user with name and password
    yield userdata['testUser1']


@pytest.fixture(scope='session', autouse=True)
def user2(userdata):
    # Existing user with name and password
    yield userdata['testUser2']


@pytest.fixture(scope='session', autouse=True)
def user3(userdata):
    # Existing user with name and password
    yield userdata['testUser3']


@pytest.fixture(scope='session', autouse=True)
def user4(userdata):
    # Existing user with name and password
    yield userdata['testUser4']


@pytest.fixture(scope='session', autouse=True)
def user5(userdata):
    # Existing user with name and password
    yield userdata['testUser5']


@pytest.fixture(scope='session', autouse=True)
def user6(userdata):
    # Existing user with name and password
    yield userdata['testUser6']


@pytest.fixture(scope='session', autouse=True)
def group1():
    # Existing Cognito group with name testGroup1
    # Add user1
    yield 'testGroup1'


@pytest.fixture(scope='session', autouse=True)
def group2():
    # Existing Cognito group with name testGroup2
    # Add user2
    yield 'testGroup2'


@pytest.fixture(scope='session', autouse=True)
def group3():
    # Existing Cognito group with name testGroup3
    # Add user3
    yield 'testGroup3'


@pytest.fixture(scope='session', autouse=True)
def group4():
    # Existing Cognito group with name testGroup4
    # Add user4
    yield 'testGroup4'


@pytest.fixture(scope='session', autouse=True)
def group5():
    # Existing Cognito group with name testGroup5
    # Add user5
    yield 'testGroup5'


@pytest.fixture(scope='session', autouse=True)
def group6():
    # Existing Cognito group with name testGroup5
    # Add user5
    yield 'testGroup6'


@pytest.fixture(scope='session')
def client1(user1) -> Client:
    yield Client(user1.username, user1.password)


@pytest.fixture(scope='session')
def client2(user2) -> Client:
    yield Client(user2.username, user2.password)


@pytest.fixture(scope='session')
def client3(user3) -> Client:
    yield Client(user3.username, user3.password)


@pytest.fixture(scope='session')
def client4(user4) -> Client:
    yield Client(user4.username, user4.password)


@pytest.fixture(scope='session')
def client5(user5) -> Client:
    yield Client(user5.username, user5.password)


@pytest.fixture(scope='session')
def client6(user6) -> Client:
    yield Client(user6.username, user6.password)


@pytest.fixture(scope='session')
def clientTenant(userTenant) -> Client:
    yield Client(userTenant.username, userTenant.password)


@pytest.fixture(scope='session')
def session_id() -> str:
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture(scope='session')
def resources_prefix(session_id) -> str:
    re.sub('[^a-zA-Z0-9-]', '', session_id).lower()
    return f'dataalltesting{session_id}'
