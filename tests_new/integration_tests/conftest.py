from dataclasses import dataclass

import pytest

from tests_new.integration_tests.client import Client


## Define user and groups fixtures - We assume they pre-exist in the AWS account.
@dataclass
class User:
    username: str
    password: str


@pytest.fixture(scope='module', autouse=True)
def userTenant():
    # Existing user with name and password
    # This user needs to belong to `DAAdministrators` group
    yield User('testUserTenant', 'Pass1Word!')


@pytest.fixture(scope='module', autouse=True)
def user1():
    # Existing user with name and password
    yield User('testUser1', 'Pass1Word!')


@pytest.fixture(scope='module', autouse=True)
def user2():
    # Existing user with name and password
    yield User('testUser2', 'Pass1Word!')


@pytest.fixture(scope='module', autouse=True)
def user3():
    # Existing user with name and password
    yield User('testUser3', 'Pass1Word!')


@pytest.fixture(scope='module', autouse=True)
def user4():
    # Existing user with name and password
    yield User('testUser4', 'Pass1Word!')


@pytest.fixture(scope='module', autouse=True)
def group1():
    # Existing Cognito group with name testGroup1
    # Add user1
    yield 'testGroup1'


@pytest.fixture(scope='module', autouse=True)
def group2():
    # Existing Cognito group with name testGroup2
    # Add user2
    yield 'testGroup2'


@pytest.fixture(scope='module', autouse=True)
def group3():
    # Existing Cognito group with name testGroup3
    # Add user3
    yield 'testGroup3'


@pytest.fixture(scope='module', autouse=True)
def group4():
    # Existing Cognito group with name testGroup4
    # Add user4
    yield 'testGroup4'


@pytest.fixture(scope='module')
def client1(user1) -> Client:
    yield Client(user1.username, user1.password)


@pytest.fixture(scope='module')
def client2(user2) -> Client:
    yield Client(user2.username, user2.password)


@pytest.fixture(scope='module')
def client3(user3) -> Client:
    yield Client(user3.username, user3.password)


@pytest.fixture(scope='module')
def client4(user4) -> Client:
    yield Client(user4.username, user4.password)


@pytest.fixture(scope='module')
def clientTenant(userTenant) -> Client:
    yield Client(userTenant.username, userTenant.password)
