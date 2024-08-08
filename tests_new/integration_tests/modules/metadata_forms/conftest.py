import pytest
from integration_tests.modules.metadata_forms.queries import create_metadata_form, delete_metadata_form


@pytest.fixture(scope='session')
def metadata_form_1(client1, group1, session_id):
    """
    Session worksheet owned by group1
    """
    mf1 = None
    try:
        input = {
            'name': 'MF Test 1',
            'description': 'first session test metadata form',
            'visibility': 'Global',
            'SamlGroupName': group1,
            'homeEntity': None,
        }
        mf1 = create_metadata_form(client1, input)
        yield mf1
    finally:
        if mf1:
            delete_metadata_form(client1, mf1.uri)
