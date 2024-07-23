import os
import pytest

from dataclasses import dataclass
from glob import glob
from dataall.base.loader import load_modules, ImportMode, list_loaded_modules
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.base.db import get_engine, create_schema_and_tables, Engine



load_modules(modes=ImportMode.all())
ENVNAME = os.environ.get('envname', 'pytest')

collect_ignore_glob = []

def ignore_module_tests_if_not_active():
    """
    Ignores tests of the modules that are turned off.
    It uses the collect_ignore_glob hook
    """
    modules = list_loaded_modules()

    all_module_files = set(glob(os.path.join('tests_new', 'unit_tests', 'modules', '[!_]*'), recursive=True))
    active_module_tests = set()
    for module in modules:
        active_module_tests.update(glob(os.path.join('tests_new', 'unit_tests', 'modules', module), recursive=True))

    exclude_tests = all_module_files - active_module_tests

    # here is a small hack to satisfy both glob and pytest. glob is using os.getcwd() which is root of the project
    # while using "make test". pytest is using test directory. Here is why we add "tests" prefix for glob and
    # remove it for pytest
    prefix_to_remove = f'tests{os.sep}'

    # migrate to remove prefix when runtime > 3.8
    exclude_tests = [excluded[len(prefix_to_remove) :] for excluded in exclude_tests]
    collect_ignore_glob.extend(exclude_tests)


ignore_module_tests_if_not_active()

pytest_plugins = [
    'unit_tests.core.permissions.global_conftest',
    'unit_tests.core.groups.global_conftest',
    'unit_tests.core.organizations.global_conftest',
    'unit_tests.core.environments.global_conftest',
]

@dataclass
class User:
    username: str


@pytest.fixture(scope='module')
def db() -> Engine:
    engine = get_engine(envname=ENVNAME)
    create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()


@pytest.fixture(scope='module', autouse=True)
def user1():
    yield User('alice')


@pytest.fixture(scope='module', autouse=True)
def user2():
    yield User('bob')

@pytest.fixture(scope='module')
def module_api_context_1(user1, group1):
    engine = get_engine(envname=ENVNAME)
    yield set_context(
        RequestContext(db_engine=engine, username=user1.username, groups=[group1.name], user_id=user1.username)
    )
    dispose_context()


@pytest.fixture(scope='function')
def api_context_1(user1, group1):
    engine = get_engine(envname=ENVNAME)
    yield set_context(
        RequestContext(db_engine=engine, username=user1.username, groups=[group1.name], user_id=user1.username)
    )
    dispose_context()


@pytest.fixture(scope='function')
def api_context_2(user2, group2):
    engine = get_engine(envname=ENVNAME)
    yield set_context(
        RequestContext(db_engine=engine, username=user2.username, groups=[group2.name], user_id=user2.username)
    )
    dispose_context()


@pytest.fixture(scope='module', autouse=True)
def patch_stack_tasks(module_mocker):
    module_mocker.patch(
        'dataall.core.stacks.aws.ecs.Ecs.is_task_running',
        return_value=False,
    )
    module_mocker.patch(
        'dataall.core.stacks.aws.ecs.Ecs.run_cdkproxy_task',
        return_value='arn:aws:eu-west-1:xxxxxxxx:ecs:task/1222222222',
    )
    module_mocker.patch(
        'dataall.core.stacks.aws.cloudformation.CloudFormation.describe_stack_resources',
        return_value=True,
    )