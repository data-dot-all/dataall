import pytest
from integration_tests.modules.dashboards.mutations import (
    import_dashboard,
    delete_dashboard,
    request_dashboard_share,
    reject_dashboard_share,
)
from integration_tests.modules.dashboards.queries import get_dashboard
from integration_tests.core.environment.utils import set_env_params
from integration_tests.modules.dashboards.aws_clients import QuickSightClient


@pytest.fixture(scope='session')
def quicksight_account_exists(session_env1, session_env1_aws_client):
    if not QuickSightClient(
        session_env1_aws_client, session_env1.AwsAccountId, session_env1.region
    ).check_enterprise_account_exists():
        pytest.skip('Skipping QuickSight tests because QuickSight account does not exist')


def create_dataall_dashboard(client, session_id, dashboard_id, env):
    dashboard_input = {
        'label': session_id,
        'dashboardId': dashboard_id,
        'environmentUri': env.environmentUri,
        'description': 'integration test dashboard',
        'SamlGroupName': env.SamlGroupName,
        'tags': [session_id],
        'terms': [],
    }
    ds = import_dashboard(client, dashboard_input)
    return get_dashboard(client, ds.dashboardUri)


@pytest.fixture(scope='session')
def dashboard1(session_id, client1, session_env1, testdata):
    set_env_params(client1, session_env1, dashboardsEnabled='true')
    dashboardId = testdata.dashboards['session_env1'].dashboardId
    ds = None
    try:
        ds = create_dataall_dashboard(client1, session_id, dashboardId, session_env1)
        yield ds
    finally:
        if ds:
            delete_dashboard(client1, ds.dashboardUri)


@pytest.fixture(scope='function')
def dashboard1_share(client1, client2, dashboard1, group2):
    share = None
    try:
        share = request_dashboard_share(client2, dashboard1.dashboardUri, group2)
        yield share
    finally:
        if share:
            reject_dashboard_share(client1, share.shareUri)
