import os
import pytest
import dataall
from dataall.base.config import config
from dataall.base.loader import load_modules, ImportMode, list_loaded_modules
from glob import glob

load_modules(modes=ImportMode.all())
ENVNAME = os.environ.get('envname', 'pytest')

collect_ignore_glob = []


def ignore_module_tests_if_not_active():
    """
    Ignores tests of the modules that are turned off.
    It uses the collect_ignore_glob hook
    """
    modules = list_loaded_modules()

    all_module_files = set(glob(os.path.join('modules', '*'), recursive=True))
    active_module_tests = set()
    for module in modules:
        active_module_tests.update(glob(os.path.join('modules', module), recursive=True))

    exclude_tests = all_module_files - active_module_tests
    collect_ignore_glob.extend(exclude_tests)


ignore_module_tests_if_not_active()


@pytest.fixture(scope='module')
def db() -> dataall.base.db.Engine:
    engine = dataall.base.db.get_engine(envname=ENVNAME)
    dataall.base.db.create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()


@pytest.fixture(scope='module')
def es():
    yield True
