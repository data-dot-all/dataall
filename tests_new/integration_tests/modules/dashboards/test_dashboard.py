from assertpy import assert_that

from integration_tests.modules.dashboards.queries import (
    search_dashboards,
    get_dashboard,
    list_dashboard_shares,
    get_author_session,
    get_reader_session,
)
from integration_tests.modules.dashboards.mutations import (
    import_dashboard,
    update_dashboard,
    delete_dashboard,
    request_dashboard_share,
    approve_dashboard_share,
    reject_dashboard_share,
)
from integration_tests.errors import GqlError


# TODO
def test_import_dashboard(client1, group1):
    pass


# TODO
def test_get_dashboard():
    pass


# TODO
def test_get_dashboard_unauthorized():
    pass


# TODO
def test_update_dashboard(client1, dashboard1):
    pass


# TODO
def test_list_dashboards():
    pass


# TODO
def test_list_dashboards_unauthorized():
    pass


# TODO
def test_request_dashboard_share():
    pass


# TODO
def test_approve_dashboard_share():
    pass


# TODO
def test_reject_dashboard_share():
    pass


# TODO
def test_get_author_session():
    pass


# TODO
def test_get_reader_session():
    pass
