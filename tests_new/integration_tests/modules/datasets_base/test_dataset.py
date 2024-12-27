import logging
from assertpy import assert_that

from integration_tests.modules.datasets_base.queries import (
    list_datasets,
    list_owned_datasets,
    list_datasets_created_in_environment,
)
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_list_datasets(  # TODO: add Redshift datasets and shared datasets
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_datasets_unauthorized(  # TODO: add Redshift datasets and shared datasets
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client2, term=session_id).nodes).is_length(0)


def test_list_owned_datasets(  # TODO: add Redshift datasets
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_owned_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_owned_datasets_unauthorized(  # TODO: add Redshift datasets
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_owned_datasets(client2, term=session_id).nodes).is_length(0)


def test_list_datasets_created_in_environment(  # TODO: add Redshift datasets
    client1,
    client2,
    session_env1,
    session_env2,
    session_s3_dataset1,
    session_imported_sse_s3_dataset1,
    session_imported_kms_s3_dataset1,
    session_id,
):
    assert_that(
        list_datasets_created_in_environment(
            client1, environment_uri=session_env1.environmentUri, term=session_id
        ).nodes
    ).is_length(3)
    assert_that(
        list_datasets_created_in_environment(
            client2, environment_uri=session_env2.environmentUri, term=session_id
        ).nodes
    ).is_length(0)


def test_list_datasets_created_in_environment_unauthorized(  # TODO: add Redshift datasets
    client2,
    session_env1,
    session_s3_dataset1,
    session_imported_sse_s3_dataset1,
    session_imported_kms_s3_dataset1,
    session_id,
):
    assert_that(list_datasets_created_in_environment).raises(GqlError).when_called_with(
        client2, environment_uri=session_env1.environmentUri, term=session_id
    ).contains('UnauthorizedOperation', 'LIST_ENVIRONMENT_DATASETS', session_env1.environmentUri)
