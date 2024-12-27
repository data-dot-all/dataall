import pytest
from assertpy import assert_that

from integration_tests.core.environment.utils import set_env_params
from integration_tests.errors import GqlError
from integration_tests.modules.dashboards.conftest import create_dataall_dashboard
from integration_tests.modules.dashboards.mutations import (
    update_dashboard,
    delete_dashboard,
    approve_dashboard_share,
    reject_dashboard_share,
)
from integration_tests.modules.dashboards.queries import (
    search_dashboards,
    get_dashboard,
    list_dashboard_shares,
    get_author_session,
    get_reader_session,
)

UPDATED_DESC = 'new description'


@pytest.mark.usefixtures('dashboards')
def test_get_author_session(client1, session_env1):
    set_env_params(client1, session_env1, dashboardsEnabled='true')
    assert_that(get_author_session(client1, session_env1.environmentUri)).starts_with('https://')


@pytest.mark.usefixtures('dashboards')
def test_get_author_session_unauthorized(client2, session_env1):
    assert_that(get_author_session).raises(GqlError).when_called_with(client2, session_env1.environmentUri).contains(
        'UnauthorizedOperation', 'CREATE_DASHBOARD', session_env1.environmentUri
    )


def test_get_dashboard(session_id, dashboard1):
    assert_that(dashboard1.label).is_equal_to(session_id)


def test_list_dashboards(client1, client2, session_id, dashboard1):
    filter = {'term': session_id}
    assert_that(search_dashboards(client1, filter).nodes).is_length(1)
    assert_that(search_dashboards(client2, filter).nodes).is_length(0)


def test_get_dashboard_unauthorized(client2, dashboard1):
    assert_that(get_dashboard(client2, dashboard1.dashboardUri)).contains_entry(restricted=None, environment=None)


def test_update_dashboard(client1, dashboard1):
    update_dashboard(client1, {'dashboardUri': dashboard1.dashboardUri, 'description': UPDATED_DESC})
    ds = get_dashboard(client1, dashboard1.dashboardUri)
    assert_that(ds.description).is_equal_to(UPDATED_DESC)


def test_update_dashboard_unauthorized(client2, dashboard1):
    assert_that(update_dashboard).raises(GqlError).when_called_with(
        client2, {'dashboardUri': dashboard1.dashboardUri, 'description': UPDATED_DESC}
    ).contains('UnauthorizedOperation', 'UPDATE_DASHBOARD', dashboard1.dashboardUri)


def test_request_dashboard_share(dashboard1_share):
    assert_that(dashboard1_share.shareUri).is_not_none()
    assert_that(dashboard1_share.status).is_equal_to('REQUESTED')


def test_list_dashboard_shares(client1, session_id, dashboard1, dashboard1_share):
    assert_that(list_dashboard_shares(client1, dashboard1.dashboardUri, {'term': session_id}).nodes).is_length(1)


def test_approve_dashboard_share_unauthorized(client2, dashboard1, dashboard1_share):
    assert_that(approve_dashboard_share).raises(GqlError).when_called_with(client2, dashboard1_share.shareUri).contains(
        'UnauthorizedOperation', 'SHARE_DASHBOARD', dashboard1.dashboardUri
    )


def test_approve_dashboard_share(client1, client2, session_id, dashboard1, dashboard1_share):
    filter = {'term': session_id}
    assert_that(search_dashboards(client2, filter).nodes).is_length(0)
    ds_share = approve_dashboard_share(client1, dashboard1_share.shareUri)
    assert_that(ds_share.status).is_equal_to('APPROVED')
    assert_that(get_reader_session(client2, dashboard1.dashboardUri)).starts_with('https://')
    assert_that(search_dashboards(client2, filter).nodes).is_length(1)


def test_reject_dashboard_share(client1, client2, session_id, dashboard1_share):
    ds_share = reject_dashboard_share(client1, dashboard1_share.shareUri)
    assert_that(ds_share.status).is_equal_to('REJECTED')
    assert_that(search_dashboards(client2, {'term': session_id}).nodes).is_length(0)


def test_get_reader_session(client1, dashboard1):
    assert_that(get_reader_session(client1, dashboard1.dashboardUri)).starts_with('https://')


def test_get_reader_session_unauthorized(client2, dashboard1):
    assert_that(get_reader_session).raises(GqlError).when_called_with(client2, dashboard1.dashboardUri).contains(
        'UnauthorizedOperation', 'GET_DASHBOARD', dashboard1.dashboardUri
    )


def test_delete_dashboard(client1, session_id, session_env1, dashboards):
    filter = {'term': session_id}
    dashboardId = dashboards['session_env1'].dashboardId
    dashboard2 = create_dataall_dashboard(client1, session_id, dashboardId, session_env1)
    assert_that(search_dashboards(client1, filter).nodes).is_length(2)

    delete_dashboard(client1, dashboard2.dashboardUri)
    assert_that(search_dashboards(client1, filter).nodes).is_length(1)


def test_delete_dashboard_unauthorized(client2, dashboard1):
    assert_that(delete_dashboard).raises(GqlError).when_called_with(client2, dashboard1.dashboardUri).contains(
        'UnauthorizedOperation', 'DELETE_DASHBOARD', dashboard1.dashboardUri
    )
