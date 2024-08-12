import pytest
from integration_tests.modules.metadata_forms.mutations import (
    create_metadata_form,
    delete_metadata_form,
    delete_metadata_form_field,
    create_metadata_form_fields,
)


@pytest.fixture(scope='session')
def metadata_form_1(client1, group1):
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


@pytest.fixture(scope='session')
def metadata_form_field_1(client1, group1, metadata_form_1):
    """
    Session worksheet owned by group1
    """
    mff = None
    try:
        input = {
            'name': 'Test Field 1',
            'description': 'test field',
            'type': 'String',
            'required': True,
            'displayNumber': 0,
        }
        mff = create_metadata_form_fields(client1, metadata_form_1.uri, [input])[0]
        yield mff
    finally:
        if mff:
            delete_metadata_form_field(client1, metadata_form_1.uri, mff.uri)