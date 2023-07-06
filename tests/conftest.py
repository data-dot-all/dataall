import os
import pytest
import dataall
from dataall.base.config import config
from dataall.base.loader import load_modules, ImportMode

load_modules(modes=ImportMode.all())
ENVNAME = os.environ.get('envname', 'pytest')

collect_ignore_glob = []


def ignore_module_tests_if_not_active():
    """
    Ignores tests of the modules that are turned off.
    It uses the collect_ignore_glob hook
    """
    modules = config.get_property('modules', {})
    for name, props in modules.items():
        if not props["active"]:
            collect_ignore_glob.append(os.path.join('modules', f'{name}', '*'))


ignore_module_tests_if_not_active()


@pytest.fixture(scope='module')
def db() -> dataall.db.Engine:
    engine = dataall.db.get_engine(envname=ENVNAME)
    dataall.db.create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()


@pytest.fixture(scope='module')
def es():
    yield True
