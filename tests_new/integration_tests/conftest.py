import os
from dataclasses import dataclass

import pytest
from dataall.base.loader import load_modules, ImportMode, list_loaded_modules
from glob import glob

from tests_new.integration_tests.client import Client

load_modules(modes=ImportMode.all())


collect_ignore_glob = []


def ignore_module_tests_if_not_active():  # TODO: maybe move to commons between tests
    """
    Ignores tests of the modules that are turned off.
    It uses the collect_ignore_glob hook
    """
    modules = list_loaded_modules()

    all_module_files = set(glob(os.path.join('tests_new', 'integration_tests', 'modules', '[!_]*'), recursive=True))
    active_module_tests = set()
    for module in modules:
        active_module_tests.update(
            glob(os.path.join('tests_new', 'integration_tests', 'modules', module), recursive=True)
        )

    exclude_tests = all_module_files - active_module_tests

    # here is a small hack to satisfy both glob and pytest. glob is using os.getcwd() which is root of the project
    # while using "make test". pytest is using test directory. Here is why we add "tests" prefix for glob and
    # remove it for pytest
    prefix_to_remove = f'tests{os.sep}'

    # migrate to remove prefix when runtime > 3.8
    exclude_tests = [excluded[len(prefix_to_remove) :] for excluded in exclude_tests]
    collect_ignore_glob.extend(exclude_tests)


ignore_module_tests_if_not_active()


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
