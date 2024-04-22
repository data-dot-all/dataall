"""update_permissions_modularization

Revision ID: 917b923f74bd
Revises: 4a0618805341
Create Date: 2023-08-23 13:06:38.450645

"""

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base

from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.base.db import Resource
from dataall.core.permissions.db.resource_policy.resource_policy_models import ResourcePolicyPermission
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicyPermission
from dataall.core.permissions.services.permission_service import PermissionService

# revision identifiers, used by Alembic.
revision = '917b923f74bd'
down_revision = '4a0618805341'
branch_labels = None
depends_on = None


Base = declarative_base()

UNUSED_RESOURCE_PERMISSIONS = [
    'LIST_DATASETS',
    'LIST_DATASET_TABLES',
    'LIST_DATASET_SHARES',
    'SUMMARY_DATASET',
    'UPLOAD_DATASET',
    'URL_DATASET',
    'STACK_DATASET',
    'SUBSCRIPTIONS_DATASET',
    'CREATE_DATASET_TABLE',
    'LIST_PIPELINES',
    'DASHBOARD_URL',
    'GET_REDSHIFT_CLUSTER',
    'SHARE_REDSHIFT_CLUSTER',
    'DELETE_REDSHIFT_CLUSTER',
    'REBOOT_REDSHIFT_CLUSTER',
    'RESUME_REDSHIFT_CLUSTER',
    'PAUSE_REDSHIFT_CLUSTER',
    'ADD_DATASET_TO_REDSHIFT_CLUSTER',
    'LIST_REDSHIFT_CLUSTER_DATASETS',
    'REMOVE_DATASET_FROM_REDSHIFT_CLUSTER',
    'ENABLE_REDSHIFT_TABLE_COPY',
    'DISABLE_REDSHIFT_TABLE_COPY',
    'GET_REDSHIFT_CLUSTER_CREDENTIALS',
    'CREATE_REDSHIFT_CLUSTER',
    'LIST_ENVIRONMENT_REDSHIFT_CLUSTERS',
]

UNUSED_TENANT_PERMISSIONS = ['MANAGE_REDSHIFT_CLUSTERS']


class Environment(Resource, Base):
    __tablename__ = 'environment'
    environmentUri = Column(String, primary_key=True)
    notebooksEnabled = Column(Boolean)
    mlStudiosEnabled = Column(Boolean)
    pipelinesEnabled = Column(Boolean)
    dashboardsEnabled = Column(Boolean)
    warehousesEnabled = Column(Boolean)


def upgrade():
    """
    The script does the following migration:
        1) Delete unused permissions
        2) Drop unused tenant_administrator table
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Deleting unused permissions...')
        delete_unused_permissions(session)

        print('Dropping tenant administrator table...')
        op.drop_table('tenant_administrator')

    except Exception as ex:
        print(f'Failed to execute the migration script due to: {ex}')
        raise ex


def downgrade():
    """
    The script does the following migration:
        1) Re-create unused permissions
        2) Re-create unused tenant_administrator table
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Migrating unused permissions...')
        save_deleted_permissions(session)

        print('Adding back tenant administrator table...')
        op.create_table(
            'tenant_administrator',
            Column('userName', String, primary_key=True, nullable=False),
            Column('tenantUri', String, nullable=False),
            Column('userRoleInTenant', String, nullable=False, default='ADMIN'),
        )
        session.commit()

    except Exception as ex:
        print(f'Failed to execute the rollback script due to: {ex}')
        raise ex


def delete_unused_permissions(session):
    for name in UNUSED_RESOURCE_PERMISSIONS:
        try:
            perm = PermissionService.get_permission_by_name(session, name, PermissionType.RESOURCE.value)
            (
                session.query(ResourcePolicyPermission)
                .filter(ResourcePolicyPermission.permissionUri == perm.permissionUri)
                .delete()
            )
            session.delete(perm)
        except Exception as ex:
            print(f'Resource Permissions Named: {name} not found and does not exist, skipping delete...')

    for name in UNUSED_TENANT_PERMISSIONS:
        try:
            perm = PermissionService.get_permission_by_name(session, name, PermissionType.TENANT.value)
            (
                session.query(TenantPolicyPermission)
                .filter(TenantPolicyPermission.permissionUri == perm.permissionUri)
                .delete()
            )
            session.delete(perm)
        except Exception as ex:
            print(f'Resource Permissions Named: {name} not found and does not exist, skipping delete...')


def save_deleted_permissions(session):
    for name in UNUSED_RESOURCE_PERMISSIONS:
        PermissionService.save_permission(session, name, name, PermissionType.RESOURCE.value)

    for name in UNUSED_TENANT_PERMISSIONS:
        PermissionService.save_permission(session, name, name, PermissionType.TENANT.value)
