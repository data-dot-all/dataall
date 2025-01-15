"""invite_env_groups_as_readers

Revision ID: 328e35e39e1e
Revises: f2f7431c34e5
Create Date: 2024-06-18 17:00:22.910461

"""

from alembic import op
from sqlalchemy import orm, Column, String
from sqlalchemy.ext.declarative import declarative_base
from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.permissions.services.organization_permissions import GET_ORGANIZATION
from dataall.core.organizations.db import organization_models as models
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.base.db import utils, Resource

# revision identifiers, used by Alembic.
revision = '328e35e39e1e'
down_revision = '448d9dc95e94'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = 'environment'
    environmentUri = Column(String, primary_key=True, default=utils.uuid('environment'))
    organizationUri = Column(String, nullable=False)


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def upgrade():
    session = get_session()
    print('Adding GET_ORGANIZATION permissions for all environment groups...')
    all_env_groups = session.query(EnvironmentGroup).all()
    envs_list = session.query(Environment).all()
    env_org = {}
    for e in envs_list:
        env_org[e.environmentUri] = e.organizationUri

    for group in all_env_groups:
        organization_uri = env_org[group.environmentUri]

        group_membership = OrganizationRepository.find_group_membership(session, [group.groupUri], organization_uri)

        if group_membership is None:
            # 1. Add Organization Group
            org_group = models.OrganizationGroup(organizationUri=organization_uri, groupUri=group.groupUri)
            session.add(org_group)

            # 2. Add Resource Policy Permissions
            permissions = [GET_ORGANIZATION]
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group.groupUri,
                resource_uri=organization_uri,
                permissions=permissions,
                resource_type=models.Organization.__name__,
            )


def downgrade():
    print('Downgrade not supported for this migration: invite env groups into otgs as readers.')
