"""update_permissions_modularization

Revision ID: 917b923f74bd
Revises: 4a0618805341
Create Date: 2023-08-23 13:06:38.450645

"""
import sqlalchemy as sa

from typing import List

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base

from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.core.permissions.db.permission_repositories import Permission
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.base.db import Resource
from dataall.core.permissions.db.permission_models import PermissionType, ResourcePolicyPermission, \
    TenantPolicyPermission
from dataall.modules.datasets.services.dataset_permissions import LIST_ENVIRONMENT_DATASETS, CREATE_DATASET


# revision identifiers, used by Alembic.
revision = '917b923f74bd'
down_revision = '4a0618805341'
branch_labels = None
depends_on = None


Base = declarative_base()

UNUSED_RESOURCE_PERMISSIONS = [
    'LIST_DATASETS', 'LIST_DATASET_TABLES', 'LIST_DATASET_SHARES', 'SUMMARY_DATASET',
    'UPLOAD_DATASET', 'URL_DATASET', 'STACK_DATASET', 'SUBSCRIPTIONS_DATASET',
    'CREATE_DATASET_TABLE', 'LIST_PIPELINES', 'DASHBOARD_URL', 'GET_REDSHIFT_CLUSTER',
    'SHARE_REDSHIFT_CLUSTER', 'DELETE_REDSHIFT_CLUSTER', 'REBOOT_REDSHIFT_CLUSTER', 'RESUME_REDSHIFT_CLUSTER',
    'PAUSE_REDSHIFT_CLUSTER', 'ADD_DATASET_TO_REDSHIFT_CLUSTER', 'LIST_REDSHIFT_CLUSTER_DATASETS',
    'REMOVE_DATASET_FROM_REDSHIFT_CLUSTER', 'ENABLE_REDSHIFT_TABLE_COPY', 'DISABLE_REDSHIFT_TABLE_COPY',
    'GET_REDSHIFT_CLUSTER_CREDENTIALS', 'CREATE_REDSHIFT_CLUSTER', 'LIST_ENVIRONMENT_REDSHIFT_CLUSTERS'
]

UNUSED_TENANT_PERMISSIONS = [
    'MANAGE_REDSHIFT_CLUSTERS'
]


def upgrade():
    """
    The script does the following migration:
        1) ....
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        migrate_groups_permissions(session)
        delete_unused_permissions(session)

        op.drop_table("tenant_administrator")

    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")
        raise ex


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        save_deleted_permissions(session)

        print("Adding Back Tenant Administrator Table")
        op.create_table(
            "tenant_administrator",
            Column("userName", String, primary_key=True, nullable=False),
            Column("tenantUri", String, nullable=False),
            Column("userRoleInTenant", String, nullable=False, default='ADMIN'),
        )
        session.commit()

    except Exception as ex:
        print(f"Failed to execute the rollback script due to: {ex}")
        raise ex


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
                resource_type=Environment.__name__
            )


def delete_unused_permissions(session):
    for name in UNUSED_RESOURCE_PERMISSIONS:
        try:
            perm = Permission.get_permission_by_name(session, name, PermissionType.RESOURCE.value)
            (
                session.query(ResourcePolicyPermission)
                .filter(ResourcePolicyPermission.permissionUri == perm.permissionUri)
                .delete()
            )
            session.delete(perm)
        except Exception as ex:
            print(f"Resource Permissions Named: {name} not found and does not exist, skipping delete...")

    for name in UNUSED_TENANT_PERMISSIONS:
        try:
            perm = Permission.get_permission_by_name(session, name, PermissionType.TENANT.value)
            (
                session.query(TenantPolicyPermission)
                .filter(TenantPolicyPermission.permissionUri == perm.permissionUri)
                .delete()
            )
            session.delete(perm)
        except Exception as ex:
            print(f"Resource Permissions Named: {name} not found and does not exist, skipping delete...")


def save_deleted_permissions(session):
    for name in UNUSED_RESOURCE_PERMISSIONS:
        Permission.save_permission(session, name, name, PermissionType.RESOURCE.value)

    for name in UNUSED_TENANT_PERMISSIONS:
        Permission.save_permission(session, name, name, PermissionType.TENANT.value)
