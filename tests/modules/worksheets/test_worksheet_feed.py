from tests.modules.feed.testhelper import FeedTestHelper
from tests.core.conftest import *
from dataall.modules.worksheets.db.models import Worksheet


@pytest.fixture(scope='module', autouse=True)
def worksheet(db):
    with db.scoped_session() as session:
        w = Worksheet(
            owner='me',
            label='xxx',
            SamlAdminGroupName='g',
        )
        session.add(w)
    return w


def test_post_message_worksheet(worksheet, client):
    FeedTestHelper(
        test_object_fixture=worksheet,
        client_fixture=client
    ).test_post_message(object_name='Worksheet', uri='worksheetUri')


def test_list_messages_worksheet(worksheet, client):
    FeedTestHelper(
        test_object_fixture=worksheet,
        client_fixture=client
    ).test_list_messages(object_name='Worksheet', uri='worksheetUri')


def test_get_target_worksheet(worksheet, client):
    FeedTestHelper(
        test_object_fixture=worksheet,
        client_fixture=client
    ).test_get_target(object_name='Worksheet', uri='worksheetUri')
