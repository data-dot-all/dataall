"""add_enviromental_parameters

Revision ID: 5fc49baecea4
Revises: d05f9a5b215e
Create Date: 2023-02-20 14:28:13.331670

"""
from typing import List

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base
from dataall.db import Resource
from dataall.db.api.permission import Permission
from dataall.db.models import TenantPolicy, TenantPolicyPermission, PermissionType
from dataall.db.permissions import MANAGE_SGMSTUDIO_NOTEBOOKS
from dataall.modules.notebooks.services.permissions import MANAGE_NOTEBOOKS

# revision identifiers, used by Alembic.
revision = "5fc49baecea4"
down_revision = "509997f0a51e"
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
        5) Migrate permissions
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print("Creating of environment_parameters table...")
        op.create_table(
            "environment_parameters",
            Column("environmentUri", String, primary_key=True),
            Column("paramKey", String, primary_key=True),
            Column("paramValue", String, nullable=False),
        )
        print("Creation of environment_parameters is done")

        print("Migrating the environmental parameters...")
        envs: List[Environment] = session.query(Environment).all()
        params: List[EnvironmentParameter] = []
        for env in envs:
            _add_param_if_exists(
                params, env, "notebooksEnabled", str(env.notebooksEnabled).lower()  # for frontend
            )

        session.add_all(params)
        print("Migration of the environmental parameters has been complete")

        op.drop_column("environment", "notebooksEnabled")
        print("Dropped the columns from the environment table ")

        print("Creating of environment_resources table...")
        op.create_table(
            "environment_resources",
            Column("environmentUri", String, primary_key=True),
            Column("resourceUri", String, primary_key=True),
            Column("resourceType", String, nullable=False),
        )
        print("Environment_resources table has been created")

        print("Filling the environment_resources table with the data")
        resources = []

        notebooks = session.query(SagemakerNotebook).all()
        for notebook in notebooks:
            _add_resource(resources, notebook.environmentUri, notebook.notebookUri, "notebook")
        session.add_all(resources)
        session.commit()

        print("Saving new MANAGE_SGMSTUDIO_NOTEBOOKS permission")
        Permission.init_permissions(session)

        manage_notebooks = Permission.get_permission_by_name(
            session, MANAGE_NOTEBOOKS, PermissionType.TENANT.name
        )
        manage_mlstudio = Permission.get_permission_by_name(
            session, MANAGE_SGMSTUDIO_NOTEBOOKS, PermissionType.TENANT.name
        )

        permissions = (
            session.query(TenantPolicyPermission)
            .filter(TenantPolicyPermission.permission == manage_notebooks.permissionUri)
            .all()
        )

        for permission in permissions:
            session.add(TenantPolicyPermission(
                sid=permission.sid,
                permissionUri=manage_mlstudio.permissionUri,
            ))
        session.commit()

    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        op.drop_table("environment_resources")
        op.add_column("environment", Column("notebooksEnabled", Boolean, default=True))

        params = session.query(EnvironmentParameter).all()
        envs = []
        for param in params:
            envs.append(Environment(
                environmentUri=param.environmentUri,
                notebooksEnabled=params["notebooksEnabled"] == "true"
            ))

        session.add_all(envs)
        op.drop_table("environment_parameters")

    except Exception as ex:
        print(f"Failed to execute the rollback script due to: {ex}")


def _add_param_if_exists(params: List[EnvironmentParameter], env: Environment, key, val) -> None:
    if val is not None:
        params.append(EnvironmentParameter(
            environmentUri=env.environmentUri,
            paramKey=key,
            paramValue=str(val).lower()
        ))


def _add_resource(resources: List[EnvironmentParameter], env_uri, uri, type) -> None:
    resources.append(EnvironmentResource(
        environmentUri=env_uri,
        resourceUri=uri,
        resourceType=type
    ))
