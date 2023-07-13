from unittest.mock import MagicMock

import pytest

from tests.api.conftest import *

@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.core.environment.api.resolvers.check_environment', return_value=True
    )
    module_mocker.patch(
        'dataall.core.environment.api.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dashboard(client, env1, org1, group, module_mocker, patch_es):
    mock_client = MagicMock()
    module_mocker.patch(
        'dataall.modules.dashboards.services.dashboard_service.DashboardQuicksightClient',
        mock_client
    )
    response = client.query(
        """
            mutation importDashboard(
                $input:ImportDashboardInput,
            ){
                importDashboard(input:$input){
                    dashboardUri
                    name
                    label
                    DashboardId
                    created
                    owner
                    SamlGroupName
                    upvotes
                    userRoleForDashboard
                }
            }
        """,
        input={
            'dashboardId': f'1234',
            'label': f'1234',
            'environmentUri': env1.environmentUri,
            'SamlGroupName': group.name,
            'terms': ['term'],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.importDashboard.owner == 'alice'
    assert response.data.importDashboard.SamlGroupName == group.name
    yield response.data.importDashboard