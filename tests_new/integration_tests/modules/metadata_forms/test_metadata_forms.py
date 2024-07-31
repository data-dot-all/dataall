from assertpy import assert_that


def test_metadata_form_create(metadata_form_1):
    assert_that(metadata_form_1).isnot_none()
    assert_that(metadata_form_1.uri).is_not_none()