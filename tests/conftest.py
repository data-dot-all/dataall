import os
import pytest
import dataall
from dataall.modules.loader import load_modules, ImportMode

load_modules(modes=[ImportMode.TASKS, ImportMode.API, ImportMode.CDK])
ENVNAME = os.environ.get('envname', 'pytest')


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
