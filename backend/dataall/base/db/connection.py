import json
import logging
import os
from contextlib import contextmanager

import sqlalchemy
from sqlalchemy.engine import reflection
from sqlalchemy.orm import sessionmaker

from dataall.base.aws.secrets_manager import SecretsManager
from dataall.base.db import Base
from dataall.base.db.dbconfig import DbConfig
from dataall.base.utils import Parameter

try:
    from urllib import quote_plus, unquote_plus
except ImportError:
    from urllib.parse import quote_plus, unquote_plus

log = logging.getLogger(__name__)
ENVNAME = os.getenv('envname', 'local')


class Engine:
    def __init__(self, dbconfig: DbConfig):
        self.dbconfig = dbconfig
        self.engine = sqlalchemy.create_engine(
            dbconfig.url,
            echo=False,
            pool_size=1,
            connect_args={'options': f'-csearch_path={dbconfig.schema}'},
        )
        try:
            if not self.engine.dialect.has_schema(self.engine, dbconfig.schema):
                log.info(f'Schema not found - init the schema {dbconfig.schema}')
                self.engine.execute(sqlalchemy.schema.CreateSchema(dbconfig.schema))
            log.info('-- Using schema: %s --', dbconfig.schema)
        except Exception as e:
            log.error(f'Could not create schema: {e}')

        self.sessions = {}
        self._session = None
        self._active_sessions = 0

    def session(self):
        if self._session is None:
            self._session = sessionmaker(bind=self.engine, autoflush=True, expire_on_commit=False)()

        return self._session

    @contextmanager
    def scoped_session(self):
        s = self.session()
        try:
            self._active_sessions += 1
            yield s
            s.commit()
        except Exception as e:
            s.rollback()
            raise e
        finally:
            self._active_sessions -= 1
            if self._active_sessions == 0:
                s.close()
                self._session = None

    def dispose(self):
        self.engine.dispose()


def create_schema_if_not_exists(engine, envname):
    print(f'Creating schema {envname}...')
    try:
        if not engine.dialect.has_schema(engine.engine, envname):
            print(f'Schema {envname} not found. Creating it...')
            engine.execute(sqlalchemy.schema.CreateSchema(envname))
    except Exception as e:
        print(f'Could not create schema: {e}')
        raise e
    print(f'Schema {envname} successfully created')
    return True


def create_schema_and_tables(engine, envname):
    drop_schema_if_exists(engine.engine, envname)
    create_schema_if_not_exists(engine.engine, envname)
    try:
        Base.metadata.create_all(engine.engine)
    except Exception as e:
        log.error(f'Failed to create all tables due to: {e}')
        raise e


def drop_schema_if_exists(engine, envname):
    try:
        if engine.dialect.has_schema(engine, envname):
            engine.execute(sqlalchemy.schema.DropSchema(envname, cascade=True))
    except Exception as e:
        log.error(f'Failed to drop all schema due to: {e}')
        raise e


def get_engine(envname=ENVNAME):
    if envname not in ['local', 'pytest', 'dkrcompose']:
        param_store = Parameter()
        credential_arn = param_store.get_parameter(env=envname, path='aurora/dbcreds')
        creds = json.loads(SecretsManager().get_secret_value(credential_arn))
        user = creds['username']
        pwd = creds['password']
        host = param_store.get_parameter(env=envname, path='aurora/hostname')
        database = param_store.get_parameter(env=envname, path='aurora/db')

        db_params = {
            'host': host,
            'db': database,
            'user': user,
            'pwd': pwd,
            'schema': envname,
        }
    else:
        db_params = {
            'host': 'db' if envname == 'dkrcompose' and os.path.exists('/.dockerenv') else 'localhost',
            'db': 'dataall',
            'user': 'postgres',
            'pwd': 'docker',
            'schema': envname,
        }
    return Engine(DbConfig(**db_params))


def has_table(table_name, engine):
    inspector = reflection.Inspector.from_engine(engine)
    tables = inspector.get_table_names()
    return table_name in tables


def has_column(schema, table, column, engine):
    inspector = reflection.Inspector.from_engine(engine)
    column_exists = False
    columns = inspector.get_columns(table_name=table, schema=schema)
    for col in columns:
        if column not in col['name']:
            continue
        column_exists = True
    return column_exists
