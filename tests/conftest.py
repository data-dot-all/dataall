import os

import dataall
import pytest

ENVNAME = os.environ.get("envname", "pytest")


@pytest.fixture(scope="module")
def db() -> dataall.db.Engine:
    engine = dataall.db.get_engine(envname=ENVNAME)
    dataall.db.create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()


@pytest.fixture(scope="module")
def es():
    yield True
