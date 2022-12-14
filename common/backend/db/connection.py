import json
import logging
import os
from contextlib import contextmanager

import boto3
import sqlalchemy
from sqlalchemy.engine import reflection
from sqlalchemy.orm import sessionmaker

from backend.utils.aws import Parameter

from .base import Base
from .common import operations
from .dbconfig import DbConfig


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
            connect_args={'options': f"-csearch_path={dbconfig.params['schema']}"},
        )
        try:
            if not self.engine.dialect.has_schema(
                self.engine, dbconfig.params['schema']
            ):
                log.info(
                    f"Schema not found - init the schema {dbconfig.params['schema']}"
                )
                self.engine.execute(
                    sqlalchemy.schema.CreateSchema(dbconfig.params['schema'])
                )
            log.info('-- Using schema: %s --', dbconfig.params['schema'])
        except Exception as e:
            log.error(f'Could not create schema: {e}')

        self.sessions = {}
        self._session = None

    def session(self):
        if self._session is None:
            self._session = sessionmaker(
                bind=self.engine, autoflush=True, expire_on_commit=False
            )()

        return self._session

    @contextmanager
    def scoped_session(self):
        s = self.session()
        try:
            yield s
            s.commit()
        except Exception as e:
            s.rollback()
            raise e
        finally:
            s.close()

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
    create_schema_if_not_exists(engine.engine, envname)
    try:
        Base.metadata.drop_all(engine.engine)
        Base.metadata.create_all(engine.engine)
    except Exception as e:
        log.error(f'Failed to create all tables due to: {e}')
        raise e


def init_permissions(engine, envname=None):
    with engine.scoped_session() as session:
        log.info('Initiating permissions')
        operations.Tenant.save_tenant(session, name='dataall', description='Tenant dataall')
        operations.Permission.init_permissions(session)


def drop_schema_if_exists(engine, envname):
    try:
        if engine.dialect.has_schema(engine, envname):
            engine.execute(sqlalchemy.schema.DropSchema(envname, cascade=True))
    except Exception as e:
        log.error(f'Failed to drop all schema due to: {e}')
        raise e


def get_engine(envname=ENVNAME):
    schema = os.getenv('schema_name', envname)
    if envname not in ['local', 'pytest', 'dkrcompose']:
        param_store = Parameter()
        credential_arn = param_store.get_parameter(env=envname, path='aurora/dbcreds')
        secretsmanager = boto3.client(
            'secretsmanager', region_name=os.environ.get('AWS_REGION', 'eu-west-1')
        )
        db_credentials_string = secretsmanager.get_secret_value(SecretId=credential_arn)
        creds = json.loads(db_credentials_string['SecretString'])
        user = creds['username']
        pwd = creds['password']
        db_params = {
            'host': param_store.get_parameter(env=envname, path='aurora/hostname'),
            'port': param_store.get_parameter(env=envname, path='aurora/port'),
            'db': param_store.get_parameter(env=envname, path='aurora/db'),
            'user': user,
            'pwd': pwd,
            'schema': schema,
        }
    else:
        hostname = 'db' if envname == 'dkrcompose' else 'localhost'
        db_params = {
            'host': hostname,
            'port': '5432',
            'db': 'dataall',
            'user': 'postgres',
            'pwd': 'docker',
            'schema': schema,
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
