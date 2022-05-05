import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ['envname'] = 'pytest'
import dataall
from src.cdkproxymain import app

ENVNAME = os.environ.get('envname', 'pytest')


@pytest.fixture(scope='module')
def cdkclient():
    yield TestClient(app)


@pytest.fixture(scope='module')
def db() -> dataall.db.Engine:
    engine = dataall.db.get_engine(envname=ENVNAME)
    dataall.db.create_schema_and_tables(engine, envname=ENVNAME)
    yield engine
    engine.session().close()
    engine.engine.dispose()
