"""add_enviromental_parameters

Revision ID: 5fc49baecea4
Revises: d05f9a5b215e
Create Date: 2023-02-20 14:28:13.331670

"""
import sqlalchemy as sa

from typing import List

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base
from dataall.db import Resource, models
from dataall.db.api import ResourcePolicy, Permission
from dataall.db.models import EnvironmentGroup, PermissionType, ResourcePolicyPermission
from dataall.modules.datasets.services.dataset_permissions import LIST_ENVIRONMENT_DATASETS, CREATE_DATASET

# revision identifiers, used by Alembic.
revision = "5fc49baecea4"
down_revision = "509997f0a51e"
branch_labels = None
depends_on = None

Base = declarative_base()

UNUSED_PERMISSIONS = ['LIST_DATASETS',  'LIST_DATASET_TABLES', 'LIST_DATASET_SHARES', 'SUMMARY_DATASET',
                      'IMPORT_DATASET', 'UPLOAD_DATASET', 'URL_DATASET', 'STACK_DATASET', 'SUBSCRIPTIONS_DATASET',
                      'CREATE_DATASET_TABLE']


class Environment(Resource, Base):
    __tablename__ = "environment"
    environmentUri = Column(String, primary_key=True)
    notebooksEnabled = Column(Boolean)
    dashboardsEnabled = Column(Boolean)


class EnvironmentParameter(Base):
    __tablename__ = "environment_parameters"
    environmentUri = Column(String, primary_key=True)
    paramKey = Column(String, primary_key=True),
    paramValue = Column(String, nullable=True)


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
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print("Creating environment_parameters table...")
        op.create_table(
            "environment_parameters",
            Column("environmentUri", String, primary_key=True),
            Column("paramKey", String, primary_key=True),
            Column("paramValue", String, nullable=False),
        )
        print("Creation of environment_parameters is done")

        print("Migrating the environmental parameters from environment table to environment_parameters table...")
        envs: List[Environment] = session.query(Environment).all()
        params: List[EnvironmentParameter] = []
        for env in envs:
            _add_param_if_exists(
                params, env, "notebooksEnabled", str(env.notebooksEnabled).lower()  # for frontend
            )
            _add_param_if_exists(
                params, env, "mlStudiosEnabled", str(env.mlStudiosEnabled).lower()  # for frontend
            )
            _add_param_if_exists(
                params, env, "dashboardsEnabled", str(env.dashboardsEnabled).lower()  # for frontend
            )

        session.add_all(params)
        print("Migration of the environmental parameters has been complete")

        op.drop_column("environment", "notebooksEnabled")
        op.drop_column("environment", "mlStudiosEnabled")
        op.drop_column("environment", "dashbaordsEnabled")
        print("Dropped the columns from the environment table ")

        create_foreign_key_to_env(op, 'sagemaker_notebook')
        create_foreign_key_to_env(op, 'dataset')
        create_foreign_key_to_env(op, 'sagemaker_studio_user_profile')
        create_foreign_key_to_env(op, 'redshiftcluster')
        create_foreign_key_to_env(op, 'datapipeline')
        create_foreign_key_to_env(op, 'dashboard')

        session.commit()

        migrate_groups_permissions(session)
        delete_unused_resource_permissions(session)

    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print("dropping foreign keys and adding columns to environment table...")

        op.drop_constraint("fk_sagemaker_notebook_env_uri", "sagemaker_notebook")
        op.drop_constraint("fk_dataset_env_uri", "dataset")
        op.drop_constraint("fk_sagemaker_studio_user_profile_env_uri", "sagemaker_studio_user_profile")
        op.drop_constraint("fk_redshiftcluster_env_uri", "redshiftcluster")
        op.drop_constraint("fk_datapipeline_env_uri", "datapipeline")
        op.drop_constraint("fk_dashboard_env_uri", "dashboard")
        op.add_column("environment", Column("notebooksEnabled", Boolean, default=True))
        op.add_column("environment", Column("mlStudiosEnabled", Boolean, default=True))
        op.add_column("environment", Column("dashbaordsEnabled", Boolean, default=True))

        print("Filling environment table with parameters rows...")
        params = session.query(EnvironmentParameter).all()
        envs = []
        for param in params:
            print(param)
            envs.append(Environment(
                environmentUri=param.environmentUri,
                notebooksEnabled=params["notebooksEnabled"] == "true",
                mlStudiosEnabled=params["mlStudiosEnabled"] == "true"
                mlStudiosEnabled=params["dashboardsEnabled"] == "true"
            ))

        for name in UNUSED_PERMISSIONS:
            Permission.save_permission(session, name, name, PermissionType.RESOURCE.value)

        session.add_all(envs)
        print("Dropping environment_parameter table...")
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


def create_foreign_key_to_env(op, table: str):
    op.create_foreign_key(
        f"fk_{table}_env_uri",
        table, "environment",
        ["environmentUri"], ["environmentUri"],
    )


def find_all_groups(session):
    return session.query(EnvironmentGroup).all()


def migrate_groups_permissions(session):
    """
    Adds new permission if the old exist. needed to get rid of old hacks in the code
    """
    permissions = [CREATE_DATASET, LIST_ENVIRONMENT_DATASETS]

    groups = find_all_groups(session)
    for group in groups:
        new_perms = []
        for existed, to_add in permissions:
            if not ResourcePolicy.has_group_resource_permission(
                session,
                group_uri=group,
                permission_name=existed,
                resource_uri=group.environmentUri,
            ):
                new_perms.append(to_add)

        if new_perms:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group.groupUri,
                permissions=new_perms,
                resource_uri=group.environmentUri,
                resource_type=models.Environment.__name__
            )


def delete_unused_resource_permissions(session):
    for name in UNUSED_PERMISSIONS:
        perm = Permission.get_permission_by_name(session, name, PermissionType.RESOURCE.value)
        (
            session.query(ResourcePolicyPermission)
            .filter(ResourcePolicyPermission.permissionUri == perm.permissionUri)
            .delete()
        )
        session.delete(perm)
