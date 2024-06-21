from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope='module', autouse=True)
def env_params():
    # Overrides environment parameters for env_fixture
    yield {'dashboardsEnabled': 'true'}


@pytest.fixture(scope='module')
def dashboard(client, env_fixture, group, module_mocker):
    mock_client = MagicMock()
    module_mocker.patch('dataall.modules.dashboards.services.dashboard_service.DashboardQuicksightClient', mock_client)
    response = client.query(
        """
            mutation importDashboard(
                $input:ImportDashboardInput!,
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
            'environmentUri': env_fixture.environmentUri,
            'SamlGroupName': group.name,
            'terms': ['term'],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.importDashboard.owner == 'alice'
    assert response.data.importDashboard.SamlGroupName == group.name
    yield response.data.importDashboard
