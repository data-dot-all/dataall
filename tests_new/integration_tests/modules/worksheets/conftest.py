import pytest
from integration_tests.modules.worksheets.queries import create_worksheet, delete_worksheet


@pytest.fixture(scope='session')
def worksheet1(client1, group1, session_id):
    """
    Session worksheet owned by group1
    """
    ws = None
    try:
        ws = create_worksheet(client1, 'worksheet1', group=group1, tags=[session_id])
        yield ws
    finally:
        if ws:
            delete_worksheet(client1, ws.worksheetUri)
