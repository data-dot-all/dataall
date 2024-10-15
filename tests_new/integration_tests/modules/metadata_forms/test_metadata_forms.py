from assertpy import assert_that

from integration_tests.modules.metadata_forms.queries import list_user_metadata_forms, get_metadata_form_full_info

from integration_tests.modules.metadata_forms.mutations import (
    update_metadata_form_fields,
    delete_metadata_form,
    delete_metadata_form_field,
)


def test_metadata_form_create(metadata_form_1):
    assert_that(metadata_form_1).is_not_none()
    assert_that(metadata_form_1.uri).is_not_none()


def test_delete_unauth(client2, metadata_form_1):
    err_message_part1 = 'An error occurred (UnauthorizedOperation) when calling DELETE_METADATA_FORM operation:'
    err_message_part2 = f'is not the owner of the metadata form {metadata_form_1.uri}'

    assert_that(delete_metadata_form).raises(Exception).when_called_with(client2, metadata_form_1.uri).contains(
        err_message_part1, err_message_part2
    )


def test_list_metadata_forms(client1, metadata_form_1):
    filter = {'page': 1, 'pageSize': 10, 'search_input': metadata_form_1.name}
    response = list_user_metadata_forms(client1, filter)
    assert_that(response.count).is_greater_than(0)

    all_uris = [item.uri for item in response.nodes]
    assert_that(all_uris).contains(metadata_form_1.uri)


def test_list_metadata_forms_access_control(client2, metadata_form_1, metadata_form_2, metadata_form_3):
    filter = {'page': 1, 'pageSize': 10}
    response = list_user_metadata_forms(client2, filter)
    all_uris = [item.uri for item in response.nodes]
    assert_that(all_uris).does_not_contain(metadata_form_2.uri)  # visibility Team Only, team = group1
    assert_that(all_uris).contains(metadata_form_1.uri)  # visibility: Global
    assert_that(all_uris).contains(metadata_form_3.uri)  # visibility: Team Only, team = group2
    # toDo: add tests for Env and Org visibility


def test_metadataform_field_create(metadata_form_field_1):
    assert_that(metadata_form_field_1).is_not_none()
    assert_that(metadata_form_field_1.uri).is_not_none()


def test_get_metadataform_full_info(client1, metadata_form_1, metadata_form_field_1):
    fullinfo = get_metadata_form_full_info(client1, metadata_form_1.uri)
    assert_that(fullinfo).is_not_none()
    assert_that(fullinfo.uri).is_equal_to(metadata_form_1.uri)

    all_field_uris = [item.uri for item in fullinfo.fields]
    assert_that(all_field_uris).contains(metadata_form_field_1.uri)


def test_create_update_field_invalid_value(client1, metadata_form_1, metadata_form_field_1):
    new_field_data = {
        'name': 'field_1',
        'metadataFormUri': metadata_form_1.uri,
        'description': 'Field 1',
        'type': 'Integer',
        'required': True,
        'possibleValues': ['wrong, not int'],
        'displayNumber': 2,
    }

    updated_field_data = {
        'uri': metadata_form_field_1.uri,
        'metadataFormUri': metadata_form_1.uri,
        'type': 'Glossary Term',
        'required': True,
        'glossaryNodeUri': 'nonexistent',
        'displayNumber': 1,
    }

    assert_that(update_metadata_form_fields).raises(Exception).when_called_with(
        client1, metadata_form_1.uri, [new_field_data]
    ).contains('InvalidInput', 'must be Integer')
    assert_that(update_metadata_form_fields).raises(Exception).when_called_with(
        client1, metadata_form_1.uri, [updated_field_data]
    ).contains('InvalidInput', 'from glossary list')


def test_delete_metadata_form_field_unauth(client2, metadata_form_1, metadata_form_field_1):
    err_message_part1 = 'An error occurred (UnauthorizedOperation) when calling DELETE_METADATA_FORM_FIELD operation:'
    err_message_part2 = f'is not the owner of the metadata form {metadata_form_1.uri}'

    assert_that(delete_metadata_form_field).raises(Exception).when_called_with(
        client2, metadata_form_1.uri, metadata_form_field_1.uri
    ).contains(err_message_part1, err_message_part2)


def test_update_metadata_form_fields_unauth(client2, metadata_form_1, metadata_form_field_1):
    field_data = {
        'name': 'field_1',
        'metadataFormUri': metadata_form_1.uri,
        'description': 'Field 1',
        'type': 'String',
        'required': True,
        'displayNumber': 1,
    }

    err_message_part1 = 'An error occurred (UnauthorizedOperation) when calling UPDATE_METADATA_FORM_FIELD operation:'
    err_message_part2 = f'is not the owner of the metadata form {metadata_form_1.uri}'

    assert_that(update_metadata_form_fields).raises(Exception).when_called_with(
        client2, metadata_form_1.uri, [field_data]
    ).contains(err_message_part1, err_message_part2)


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
