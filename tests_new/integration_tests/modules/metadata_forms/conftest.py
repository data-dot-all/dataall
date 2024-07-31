import pytest
from integration_tests.modules.metadata_forms.queries import create_metadata_form


@pytest.fixture(scope='session')
def metadata_form_1(client1, group1, session_id):
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
