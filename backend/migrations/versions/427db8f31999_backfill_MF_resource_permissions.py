"""backfill_MF_resource_permissions

Revision ID: 427db8f31999
Revises: f87aecc36d39
Create Date: 2024-09-11 15:55:51.444403

"""

from alembic import op
from sqlalchemy import orm, Column, String
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils, Resource
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.resources_permissions import RESOURCES_ALL_WITH_DESC
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.metadata_forms.services.metadata_form_permissions import (
    ATTACH_METADATA_FORM,
    CREATE_METADATA_FORM,
    METADATA_FORM_PERMISSIONS_ALL,
)

# revision identifiers, used by Alembic.
revision = '427db8f31999'
down_revision = 'f87aecc36d39'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = 'environment'
    organizationUri = Column(String, nullable=False)
    environmentUri = Column(String, primary_key=True, default=utils.uuid('environment'))
    SamlGroupName = Column(String, nullable=False)


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
    orgs = session.query(Organization).all()
    for org in orgs:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=org.SamlGroupName,
            resource_uri=org.organizationUri,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
            resource_type=Organization.__name__,
        )
    print('Adding environment resource permissions...')
    envs = session.query(Environment).all()
    for env in envs:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=env.SamlGroupName,
            resource_uri=env.environmentUri,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
            resource_type=Environment.__name__,
        )
    print('Adding dataset resource permissions...')
    datasets = session.query(DatasetBase).all()
    for dataset in datasets:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            resource_uri=dataset.datasetUri,
            permissions=[ATTACH_METADATA_FORM],
            resource_type=DatasetBase.__name__,
        )


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    all_environments = session.query(Environment).all()
    for env in all_environments:
        policies = ResourcePolicyService.find_resource_policies(
            session=session,
            group=env.SamlGroupName,
            resource_uri=env.environmentUri,
            resource_type=Environment.__name__,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
        )
        for policy in policies:
            for resource_pol_permission in policy.permissions:
                if resource_pol_permission.permission.name in [ATTACH_METADATA_FORM, CREATE_METADATA_FORM]:
                    session.delete(resource_pol_permission)
                    session.commit()

    all_organizations = session.query(Organization).all()
    for org in all_organizations:
        policies = ResourcePolicyService.find_resource_policies(
            session=session,
            group=org.SamlGroupName,
            resource_uri=org.organizationUri,
            permissions=[ATTACH_METADATA_FORM, CREATE_METADATA_FORM],
            resource_type=Organization.__name__,
        )
        for policy in policies:
            for resource_pol_permission in policy.permissions:
                if resource_pol_permission.permission.name in [ATTACH_METADATA_FORM, CREATE_METADATA_FORM]:
                    session.delete(resource_pol_permission)
                    session.commit()

    datasets = session.query(DatasetBase).all()
    for dataset in datasets:
        policies = ResourcePolicyService.find_resource_policies(
            session=session,
            group=dataset.SamlAdminGroupName,
            resource_uri=dataset.datasetUri,
            permissions=[ATTACH_METADATA_FORM],
            resource_type=DatasetBase.__name__,
        )

        for policy in policies:
            for resource_pol_permission in policy.permissions:
                if resource_pol_permission.permission.name in [ATTACH_METADATA_FORM, CREATE_METADATA_FORM]:
                    session.delete(resource_pol_permission)
                    session.commit()
