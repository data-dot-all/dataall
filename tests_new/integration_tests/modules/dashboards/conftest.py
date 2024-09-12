import pytest
from integration_tests.modules.dashboards.mutations import import_dashboard, delete_dashboard


@pytest.fixture(scope='session')
def dashboard1(client1, group1, session_id):
    """
    Session worksheet owned by group1
    """
    ds = None
    try:
        ds = import_dashboard(client1, 'dashboard1', group=group1, tags=[session_id])
        yield ds
    finally:
        if ds:
            delete_dashboard(client1, ds.dashboardUri)
