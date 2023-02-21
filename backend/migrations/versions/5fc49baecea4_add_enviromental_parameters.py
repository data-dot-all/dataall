"""add_enviromental_parameters

Revision ID: 5fc49baecea4
Revises: d05f9a5b215e
Create Date: 2023-02-20 14:28:13.331670

"""
from typing import List

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base
from dataall.db.api.permission import Permission
from dataall.db import Resource


# revision identifiers, used by Alembic.
revision = "5fc49baecea4"
down_revision = "d05f9a5b215e"
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = "environment"
    environmentUri = Column(String, primary_key=True)
    notebooksEnabled = Column(Boolean)


class EnvironmentParameter(Resource, Base):
    __tablename__ = "environment_parameters"
    environmentUri = Column(String, primary_key=True)
    paramKey = Column(String, primary_key=True),
    paramValue = Column(String, nullable=True)


class EnvironmentResource(Resource, Base):
    __tablename__ = "environment_resources"
    environmentUri = Column(String, primary_key=True)
    resourceUri = (Column(String, primary_key=True),)
    resourceType = Column(String, nullable=False)


class SagemakerNotebook(Resource, Base):
    __tablename__ = "sagemaker_notebook"
    environmentUri = Column(String, nullable=False)
    notebookUri = Column(String, primary_key=True)


def upgrade():
    """
    The script does the following migration:
        1) creation of the environment_parameters and environment_resources tables
        2) Migration xxxEnabled to the environment_parameters table
        3) Dropping the xxxEnabled columns from the environment_parameters
        4) Migration every resource allocated for the environment to the environment_resources
        5) Updates the permissions
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print("Creating of environment_parameters table...")
        op.create_table(
            "environment_parameters",
            Column("environmentUri", String, primary_key=True),
            Column("paramKey", String, primary_key=True),
            Column("paramValue", String, nullable=True),
        )
        print("Creation of environment_parameters is done")

        print("Migrating the environmental parameters...")
        envs: List[Environment] = session.query(Environment).all()
        params: List[EnvironmentParameter] = []
        for env in envs:
            _add_param_if_exists(params, env, "notebooksEnabled", env.notebooksEnabled)

        session.add_all(params)
        print("Migration of the environmental parameters has been complete")

        op.drop_column("environment", "notebooksEnabled")
        print("Dropped the columns from the environment table ")

        print("Creating of environment_resources table...")
        op.create_table(
            "environment_resources",
            Column("environmentUri", String, primary_key=True),
            Column("resourceUri", String, primary_key=True),
            Column("resourceType", String, nullable=True),
        )
        print("Environment_resources table has been created")

        print("Filling the environment_resources table with the data")
        resources = []

        notebooks = session.query(SagemakerNotebook).all()
        for notebook in notebooks:
            _add_resource(resources, notebook.environmentUri, notebook.notebookUri, "notebook")

        session.commit()

    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")


def downgrade():
    # TODO: complete the rollback
    op.drop_table("environment_resources")


def _add_param_if_exists(params: List[EnvironmentParameter], env: Environment, key, val) -> None:
    if val is not None:
        params.append(EnvironmentParameter(environmentUri=env.environmentUri, paramKey=key, paramValue=str(val)))


def _add_resource(resources: List[EnvironmentParameter], envUri, uri, type) -> None:
    resources.append(EnvironmentResource(environmentUri=envUri, resourceUri=uri, resourceType=type))
