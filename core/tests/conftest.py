import os
import pytest
from common.backend import db

ENVNAME = os.environ.get('envname', 'pytest')


@pytest.fixture(scope='module')
def db() -> db.Engine:
    engine = db.get_engine(envname=ENVNAME)
    db.create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()


@pytest.fixture(scope='module')
def es():
    yield True
