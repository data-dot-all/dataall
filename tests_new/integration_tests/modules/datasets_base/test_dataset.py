import logging
from assertpy import assert_that

from integration_tests.modules.datasets_base.queries import (
    list_datasets,
    list_owned_datasets,
    list_datasets_created_in_environment,
)

log = logging.getLogger(__name__)


def test_list_datasets(
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_datasets_unauthorized(
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client2, term=session_id).nodes).is_length(0)


def test_list_owned_datasets(  # TODO
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_owned_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_owned_datasets_unauthorized(  # TODO
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_owned_datasets(client2, term=session_id).nodes).is_length(0)


def test_list_datasets_created_in_environment():
    # TODO
    pass


def test_list_datasets_created_in_environment_unauthorized():
    # TODO
    pass
