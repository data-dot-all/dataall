from assertpy import assert_that

from integration_tests.modules.metadata_forms.queries import list_metadata_forms


def test_metadata_form_create(metadata_form_1):
    assert_that(metadata_form_1).is_not_none()
    assert_that(metadata_form_1.uri).is_not_none()


def test_list_metadata_forms(client1, metadata_form_1):
    filter = {'page': 1, 'pageSize': 10}
    response = list_metadata_forms(client1, filter)
    assert_that(response.count).is_greater_than(0)

    all_uris = [item.uri for item in response.nodes]
    assert_that(all_uris).contains(metadata_form_1.uri)
