import pytest
from .queries import archive_organization, create_organization, invite_team_to_organization, update_tenant_permissions


@pytest.fixture(scope='module', autouse=True)
def create_organization_fixture():
    cache = {}

    def factory(client, name, owner, group):
        key = name + owner + group
        if cache.get(key):
            print(f'returning item from cached key {key}')
            return cache.get(key)

        response = create_organization(client, name, group)
        cache[key] = response.data.createOrganization
        return cache[key]

    yield factory


@pytest.fixture(scope='module')
def organization1(client1, user1, group1, create_organization_fixture):
    # organization.SamlAdminGroup = group1
    org = create_organization_fixture(client1, 'organization1', user1.username, group1)
    yield org
    archive_organization(client1, org.organizationUri)


@pytest.fixture(scope='module')
def organization2_with_invited_group2(client1, user1, group1, create_organization_fixture, group2):
    org = create_organization_fixture(client1, 'organization2', user1.username, group1)
    invite_team_to_organization(client=client1, organizationUri=org.organizationUri, group=group2)
    yield org
    archive_organization(client1, org.organizationUri)


@pytest.fixture(scope='module')
def client_noTenantPermissions(clientTenant, group4, client4):
    permissions = ['MANAGE_OTHER_THINGS']
    update_tenant_permissions(client=clientTenant, group=group4, permissions=permissions)
    yield client4
    update_tenant_permissions(clientTenant, group4, ['MANAGE_ORGANIZATIONS'])
