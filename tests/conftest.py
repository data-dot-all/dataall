import os
from dataclasses import dataclass
from glob import glob
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from dataall.base.config import config
from dataall.base.db import get_engine, create_schema_and_tables, Engine
from dataall.base.loader import load_modules, ImportMode, list_loaded_modules
from dataall.core.groups.db.group_models import Group
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from tests.client import create_app, ClientWrapper

for module in config.get_property('modules'):
    config.set_property(f'modules.{module}.active', True)

load_modules(modes=ImportMode.all())
ENVNAME = os.environ.get('envname', 'pytest')

collect_ignore_glob = []


def ignore_module_tests_if_not_active():
    """
    Ignores tests of the modules that are turned off.
    It uses the collect_ignore_glob hook
    """
    modules = list_loaded_modules()

    all_module_files = set(glob(os.path.join('tests', 'modules', '[!_]*'), recursive=True))
    active_module_tests = set()
    for module in modules:
        active_module_tests.update(glob(os.path.join('tests', 'modules', module), recursive=True))

    exclude_tests = all_module_files - active_module_tests

    # here is a small hack to satisfy both glob and pytest. glob is using os.getcwd() which is root of the project
    # while using "make test". pytest is using test directory. Here is why we add "tests" prefix for glob and
    # remove it for pytest
    prefix_to_remove = f'tests{os.sep}'

    # migrate to remove prefix when runtime > 3.8
    exclude_tests = [excluded[len(prefix_to_remove) :] for excluded in exclude_tests]
    collect_ignore_glob.extend(exclude_tests)


ignore_module_tests_if_not_active()


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


@pytest.fixture(scope='module')
def es():
    yield True


@pytest.fixture(scope='module', autouse=True)
def app(db):
    yield create_app(db)


@pytest.fixture(scope='module')
def client(app) -> ClientWrapper:
    with TestClient(app) as client:
        yield ClientWrapper(client)


@pytest.fixture(scope='module', autouse=True)
def user():
    yield User('alice')


@pytest.fixture(scope='module', autouse=True)
def user2():
    yield User('bob')


@pytest.fixture(scope='module', autouse=True)
def user3():
    yield User('david')


@pytest.fixture(scope='module', autouse=True)
def userNoTenantPermissions():
    yield User('noPermissionsUser')


def _create_group(db, tenant, name, user, attach_permissions=True):
    with db.scoped_session() as session:
        group = Group(name=name, label=name, owner=user.username)
        session.add(group)
        session.commit()

        if attach_permissions:
            TenantPolicyService.attach_group_tenant_policy(
                session=session,
                group=name,
                permissions=TENANT_ALL,
                tenant_name=tenant.name,
            )
        return group


@pytest.fixture(scope='module')
def group(db, tenant, user):
    yield _create_group(db, tenant, 'testadmins', user)


@pytest.fixture(scope='module')
def group2(db, tenant, user2):
    yield _create_group(db, tenant, 'dataengineers', user2)


@pytest.fixture(scope='module')
def group3(db, tenant, user3):
    yield _create_group(db, tenant, 'datascientists', user3)


@pytest.fixture(scope='module')
def group4(db, tenant, user3):
    yield _create_group(db, tenant, 'externals', user3)


@pytest.fixture(scope='module')
def not_in_org_group(db, tenant, user):
    yield _create_group(db, tenant, 'NotInOrgGroup', user)


@pytest.fixture(scope='module')
def groupNoTenantPermissions(db, tenant, userNoTenantPermissions):
    yield _create_group(db, tenant, 'groupNoTenantPermissions', userNoTenantPermissions, attach_permissions=False)


@pytest.fixture(scope='module', autouse=True)
def tenant(db, permissions):
    with db.scoped_session() as session:
        tenant = TenantPolicyService.save_tenant(session, name='dataall', description='Tenant dataall')
        yield tenant


@pytest.fixture(scope='module', autouse=True)
def patch_request(module_mocker):
    """we will mock requests.post so no call to cdk proxy will be made"""
    module_mocker.patch('requests.post', return_value=True)


@pytest.fixture(scope='module', autouse=True)
def permissions(db):
    with db.scoped_session() as session:
        yield PermissionService.init_permissions(session)


@pytest.fixture(scope='function', autouse=True)
def patch_ssm(mocker):
    mocker.patch('dataall.base.utils.parameter.Parameter.get_parameter', return_value='param')


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


@pytest.fixture(scope='module', autouse=True)
def patch_check_env(module_mocker):
    module_mocker.patch(
        'dataall.core.environment.services.environment_service.EnvironmentService._check_cdk_resources',
        return_value='CDKROLENAME',
    )
    module_mocker.patch(
        'dataall.core.environment.services.environment_service.EnvironmentService._get_pivot_role_as_part_of_environment',
        return_value=False,
    )


@pytest.fixture(scope='function')
def mock_aws_client(module_mocker):
    aws_client = MagicMock()
    session_helper = MagicMock()
    session = MagicMock()

    # there can be other mocker clients
    module_mocker.patch('dataall.modules.s3_datasets.aws.s3_dataset_client.SessionHelper', session_helper)

    module_mocker.patch('dataall.modules.s3_datasets.aws.kms_dataset_client.SessionHelper', session_helper)

    module_mocker.patch('dataall.base.aws.sts.SessionHelper', session_helper)

    session_helper.get_session.return_value = session
    session_helper.remote_session.return_value = session
    session.client.return_value = aws_client

    yield aws_client
