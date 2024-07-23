import pytest

from dataall.core.organizations.services.organization_service import OrganizationService

@pytest.fixture(scope='module')
def org1(module_api_context_1, user1, group1):
    org = OrganizationService.create_organization(data={
        'label': 'testorg',
        'SamlGroupName': group1.name
    })
    yield org

