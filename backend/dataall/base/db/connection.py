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
            connect_args={'options': f'-c search_path={dbconfig.schema}'},
        )
        try:
            create_schema_if_not_exists(self.engine, dbconfig.schema)
            log.info('-- Using schema: %s --', dbconfig.schema)
        except Exception as e:
            log.exception('Could not create schema')

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
    try:
        with engine.engine.connect() as connection:
            if not sqlalchemy.inspect(connection).has_schema(envname):
                log.info(f'Schema {envname} not found. Creating it...')
                connection.execute(sqlalchemy.schema.CreateSchema(envname))
                connection.commit()
            else:
                log.info(f'Schema {envname} already exists')
    except Exception as e:
        log.exception('Could not create schema')
        raise e
    return True


def create_schema_and_tables(engine, envname):
    drop_schema_if_exists(engine.engine, envname)
    create_schema_if_not_exists(engine.engine, envname)
    try:
        Base.metadata.create_all(engine.engine)
    except Exception as e:
        log.exception('Failed to create all tables')
        raise e


def drop_schema_if_exists(engine, envname):
    try:
        with engine.engine.connect() as connection:
            if sqlalchemy.inspect(connection).has_schema(envname):
                log.warning(f'Dropping schema {envname}')
                connection.execute(sqlalchemy.schema.DropSchema(envname, cascade=True))
                connection.commit()
    except Exception as e:
        log.exception('Failed to drop schema')
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
