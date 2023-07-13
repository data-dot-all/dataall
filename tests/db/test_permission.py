import pytest

import dataall
from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization, OrganisationUserRole
from dataall.core.permissions.db.permission import Permission
from dataall.core.permissions.db.permission_models import PermissionType
from dataall.core.permissions.db.tenant import Tenant
from dataall.core.permissions.db.tenant_policy import TenantPolicy
from dataall.db import exceptions
from dataall.db.permissions import MANAGE_GROUPS, ENVIRONMENT_ALL, ORGANIZATION_ALL


def permissions(db, all_perms):
    with db.scoped_session() as session:
        permissions = []
        for p in all_perms:
            permissions.append(
                Permission.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )
        for p in dataall.db.permissions.TENANT_ALL:
            permissions.append(
                Permission.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.TENANT.name,
                )
            )
        session.commit()


@pytest.fixture(scope='module')
def tenant(db):
    with db.scoped_session() as session:
        tenant = Tenant.save_tenant(
            session, name='dataall', description='Tenant dataall'
        )
        yield tenant


@pytest.fixture(scope='module')
def group(db, user):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(
            name='testadmins', label='testadmins', owner='alice'
        )
        session.add(group)
        yield group


@pytest.fixture(scope='module', autouse=True)
def org(db, group):
    with db.scoped_session() as session:
        org = Organization(
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName=group.name,
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module', autouse=True)
def env(org, db, group):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org.organizationUri,
            AwsAccountId='12345678901',
            region='eu-west-1',
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName=group.name,
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment='999',
        )
        session.add(env)
    yield env


def test_attach_tenant_policy(db, user, group, tenant):
    permissions(db, ORGANIZATION_ALL + ENVIRONMENT_ALL)
    with db.scoped_session() as session:
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_GROUPS],
            tenant_name='dataall',
        )

        assert TenantPolicy.check_user_tenant_permission(
            session=session,
            username=user.userName,
            groups=[group.name],
            permission_name=MANAGE_GROUPS,
            tenant_name='dataall',
        )


def test_unauthorized_tenant_policy(db, user, group):
    with pytest.raises(exceptions.TenantUnauthorized):
        with db.scoped_session() as session:
            assert TenantPolicy.check_user_tenant_permission(
                session=session,
                username=user.userName,
                groups=[group.name],
                permission_name='UNKNOW_PERMISSION',
                tenant_name='dataall',
            )
