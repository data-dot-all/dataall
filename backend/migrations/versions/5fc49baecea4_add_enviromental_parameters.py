"""add_enviromental_parameters

Revision ID: 5fc49baecea4
Revises: e1cd4927482b
Create Date: 2023-02-20 14:28:13.331670

"""

from typing import List

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base

from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.base.db import Resource

# revision identifiers, used by Alembic.
revision = '5fc49baecea4'
down_revision = 'e1cd4927482b'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = 'environment'
    environmentUri = Column(String, primary_key=True)
    notebooksEnabled = Column(Boolean)
    mlStudiosEnabled = Column(Boolean)
    pipelinesEnabled = Column(Boolean)
    dashboardsEnabled = Column(Boolean)
    warehousesEnabled = Column(Boolean)


class EnvironmentParameter(Base):
    __tablename__ = 'environment_parameters'
    environmentUri = Column(String, primary_key=True)
    key = Column('paramKey', String, primary_key=True)
    value = Column('paramValue', String, nullable=True)

    def __init__(self, env_uri, key, value):
        super().__init__()
        self.environmentUri = env_uri
        self.key = key
        self.value = value


def upgrade():
    """
    The script does the following migration:
        1) creation of the environment_parameters and environment_resources tables
        2) Migration xxxEnabled to the environment_parameters table
        3) Dropping the xxxEnabled columns from the environment_parameters
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Creating environment_parameters table...')
        op.create_table(
            'environment_parameters',
            Column('environmentUri', String, primary_key=True),
            Column('paramKey', String, primary_key=True),
            Column('paramValue', String, nullable=False),
        )
        print('Creation of environment_parameters table is done')

        print('Migrating the environmental parameters from environment table to environment_parameters table...')
        envs: List[Environment] = session.query(Environment).all()
        params: List[EnvironmentParameter] = []
        for env in envs:
            _add_param_if_exists(
                params,
                env,
                'notebooksEnabled',
                str(env.notebooksEnabled).lower(),  # for frontend
            )
            _add_param_if_exists(
                params,
                env,
                'mlStudiosEnabled',
                str(env.mlStudiosEnabled).lower(),  # for frontend
            )
            _add_param_if_exists(
                params,
                env,
                'pipelinesEnabled',
                str(env.pipelinesEnabled).lower(),  # for frontend
            )
            _add_param_if_exists(
                params,
                env,
                'dashboardsEnabled',
                str(env.dashboardsEnabled).lower(),  # for frontend
            )

        session.add_all(params)
        print('Migration of the environmental parameters has been complete')

        op.drop_column('environment', 'notebooksEnabled')
        op.drop_column('environment', 'mlStudiosEnabled')
        op.drop_column('environment', 'pipelinesEnabled')
        op.drop_column('environment', 'dashboardsEnabled')
        op.drop_column('environment', 'warehousesEnabled')
        print('Dropped the columns from the environment table ')

        create_foreign_key_to_env(op, 'sagemaker_notebook')
        create_foreign_key_to_env(op, 'dataset')
        create_foreign_key_to_env(op, 'sagemaker_studio_user_profile')
        create_foreign_key_to_env(op, 'redshiftcluster')
        create_foreign_key_to_env(op, 'datapipeline')
        create_foreign_key_to_env(op, 'dashboard')

        session.commit()

    except Exception as ex:
        print(f'Failed to execute the migration script due to: {ex}')
        raise ex


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('dropping foreign keys and adding columns to environment table...')

        op.drop_constraint('fk_sagemaker_notebook_env_uri', 'sagemaker_notebook')
        op.drop_constraint('fk_dataset_env_uri', 'dataset')
        op.drop_constraint('fk_sagemaker_studio_user_profile_env_uri', 'sagemaker_studio_user_profile')
        op.drop_constraint('fk_redshiftcluster_env_uri', 'redshiftcluster')
        op.drop_constraint('fk_datapipeline_env_uri', 'datapipeline')
        op.drop_constraint('fk_dashboard_env_uri', 'dashboard')
        op.add_column('environment', Column('notebooksEnabled', Boolean, default=True))
        op.add_column('environment', Column('mlStudiosEnabled', Boolean, default=True))
        op.add_column('environment', Column('pipelinesEnabled', Boolean, default=True))
        op.add_column('environment', Column('dashboardsEnabled', Boolean, default=True))
        op.add_column('environment', Column('warehousesEnabled', Boolean, default=True))

        print('Filling environment table with parameters rows...')
        envs_all = session.query(Environment).all()
        envs = []
        for env in envs_all:
            params = session.query(EnvironmentParameter).filter(
                EnvironmentParameter.environmentUri == EnvironmentParameter.environmentUri
            )
            env_params = {}
            for param in params:
                env_params[param.key] = param.value == 'true'
            print(env_params)

            env.notebooksEnabled = env_params.get('notebooksEnabled', False)
            env.mlStudiosEnabled = env_params.get('mlStudiosEnabled', False)
            env.pipelinesEnabled = env_params.get('pipelinesEnabled', False)
            env.dashboardsEnabled = env_params.get('dashboardsEnabled', False)
            env.warehousesEnabled = env_params.get('warehousesEnabled', False)
            session.commit()

        print('Dropping environment_parameter table...')
        op.drop_table('environment_parameters')

        session.commit()

    except Exception as ex:
        print(f'Failed to execute the rollback script due to: {ex}')
        raise ex


def _add_param_if_exists(params: List[EnvironmentParameter], env: Environment, key, val) -> None:
    if val is not None:
        params.append(EnvironmentParameter(env.environmentUri, key, str(val).lower()))


def create_foreign_key_to_env(op, table: str):
    op.create_foreign_key(
        f'fk_{table}_env_uri',
        table,
        'environment',
        ['environmentUri'],
        ['environmentUri'],
    )


def find_all_groups(session):
    return session.query(EnvironmentGroup).all()
