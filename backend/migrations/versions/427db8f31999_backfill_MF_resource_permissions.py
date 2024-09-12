"""backfill_MF_resource_permissions

Revision ID: 427db8f31999
Revises: f87aecc36d39
Create Date: 2024-09-11 15:55:51.444403

"""
from alembic import op
from sqlalchemy import orm

from dataall.core.environment.db.environment_models import EnvironmentGroup, Environment
from dataall.core.organizations.db.organization_models import OrganizationGroup, Organization
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.resources_permissions import RESOURCES_ALL_WITH_DESC
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.metadata_forms.services.metadata_form_permissions import ATTACH_METADATA_FORM, \
    CREATE_METADATA_FORM, METADATA_FORM_PERMISSIONS_ALL

# revision identifiers, used by Alembic.
revision = '427db8f31999'
down_revision = 'f87aecc36d39'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def upgrade():
    session = get_session()

    for perm in [ATTACH_METADATA_FORM, CREATE_METADATA_FORM] + METADATA_FORM_PERMISSIONS_ALL:
        PermissionService.save_permission(
            session,
            name=perm,
            description=RESOURCES_ALL_WITH_DESC.get(perm, perm),
            permission_type=PermissionType.RESOURCE.name,
        )
    print('Adding organization resource permissions...')
    orgGroups = session.query(OrganizationGroup).all()
    for group in orgGroups:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.groupUri,
            resource_uri=group.organizationUri,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
            resource_type=Organization.__name__,
        )
    print('Adding environment resource permissions...')
    envGroups = session.query(EnvironmentGroup).all()
    for group in envGroups:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.groupUri,
            resource_uri=group.environmentUri,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
            resource_type=Environment.__name__,
        )
    print('Adding dataset resource permissions...')
    datasets = session.query(DatasetBase).all()
    for dataset in datasets:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=dataset.SamlGroupName,
            resource_uri=dataset.datasetUri,
            permissions=[ATTACH_METADATA_FORM],
            resource_type=DatasetBase.__name__,
        )


def downgrade():
    print('no downgrade supported')
