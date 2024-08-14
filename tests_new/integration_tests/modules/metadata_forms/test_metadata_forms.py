from assertpy import assert_that

from integration_tests.modules.metadata_forms.queries import list_metadata_forms, get_metadata_form_full_info
from integration_tests.modules.metadata_forms.mutations import update_metadata_form_fields


def test_metadata_form_create(metadata_form_1):
    assert_that(metadata_form_1).is_not_none()
    assert_that(metadata_form_1.uri).is_not_none()


def test_list_metadata_forms(client1, metadata_form_1):
    filter = {'page': 1, 'pageSize': 10, 'search_input': metadata_form_1.name}
    response = list_metadata_forms(client1, filter)
    assert_that(response.count).is_greater_than(0)

    all_uris = [item.uri for item in response.nodes]
    assert_that(all_uris).contains(metadata_form_1.uri)


def test_metadataform_field_create(metadata_form_field_1):
    assert_that(metadata_form_field_1).is_not_none()
    assert_that(metadata_form_field_1.uri).is_not_none()


def test_get_metadataform_full_info(client1, metadata_form_1, metadata_form_field_1):
    fullinfo = get_metadata_form_full_info(client1, metadata_form_1.uri)
    assert_that(fullinfo).is_not_none()
    assert_that(fullinfo.uri).is_equal_to(metadata_form_1.uri)

    all_field_uris = [item.uri for item in fullinfo.fields]
    assert_that(all_field_uris).contains(metadata_form_field_1.uri)


def test_metadata_form_fields_batch(client1, metadata_form_1, metadata_form_field_1):
    fullinfo_before = get_metadata_form_full_info(client1, metadata_form_1.uri)

    field_data_1 = {
        'name': 'field_1',
        'metadataFormUri': metadata_form_1.uri,
        'description': 'Field 1',
        'type': 'String',
        'required': True,
        'displayNumber': 1,
    }
    field_data_2 = {
        'name': 'field_2',
        'metadataFormUri': metadata_form_1.uri,
        'description': 'Field 2',
        'type': 'Integer',
        'required': False,
        'displayNumber': 2,
    }
    field_data_3 = {
        'name': 'field_3',
        'metadataFormUri': metadata_form_1.uri,
        'description': 'Field 3',
        'type': 'Boolean',
        'required': False,
        'displayNumber': 3,
    }

    new_fields = [field_data_1, field_data_2, field_data_3]
    all_fields = update_metadata_form_fields(client1, metadata_form_1.uri, new_fields)
    fullinfo_after = get_metadata_form_full_info(client1, metadata_form_1.uri)

    assert_that(len(fullinfo_after.fields)).is_equal_to(len(fullinfo_before.fields) + len(new_fields))

    for f in all_fields:
        if f['uri'] != metadata_form_field_1.uri:
            f['deleted'] = True

    update_metadata_form_fields(client1, metadata_form_1.uri, all_fields)
    fullinfo_after_delete = get_metadata_form_full_info(client1, metadata_form_1.uri)
    assert_that(len(fullinfo_after_delete.fields)).is_equal_to(len(fullinfo_before.fields))
