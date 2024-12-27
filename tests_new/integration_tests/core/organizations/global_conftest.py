import pytest
from .queries import archive_organization, create_organization, invite_team_to_organization, update_tenant_permissions


@pytest.fixture(scope='session')
def org1(client1, group1, group5, session_id):
    """
    Session org owned by group1
    """
    org = create_organization(client1, 'organization1', group1, tags=[session_id])
    invite_team_to_organization(
        client=client1,
        organizationUri=org.organizationUri,
        group=group5,
        permissions=['LINK_ENVIRONMENT', 'INVITE_ORGANIZATION_GROUP', 'REMOVE_ORGANIZATION_GROUP'],
    )
    yield org
    archive_organization(client1, org.organizationUri)


@pytest.fixture(scope='session')
def org2(client1, group1, group2, group3, session_id):
    """
    Session org owned by group1 and invite group2
    """
    org = create_organization(client1, 'organization2', group1, tags=[session_id])
    invite_team_to_organization(client=client1, organizationUri=org.organizationUri, group=group2)
    invite_team_to_organization(client=client1, organizationUri=org.organizationUri, group=group3)
    yield org
    archive_organization(client1, org.organizationUri)


@pytest.fixture
def client_noTenantPermissions(clientTenant, client4, group4):
    permissions = ['MANAGE_GROUPS']
    update_tenant_permissions(client=clientTenant, group=group4, permissions=permissions)
    yield client4
    update_tenant_permissions(clientTenant, group4, ['MANAGE_ORGANIZATIONS'])
