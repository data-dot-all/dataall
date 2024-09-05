import logging
import os
import json
from datetime import datetime
import time
from assertpy import assert_that
import requests

from integration_tests.modules.s3_datasets.queries import (
    delete_dataset,
    get_dataset,
    get_dataset_assume_role_url,
    generate_dataset_access_token,
    get_dataset_presigned_role_url,
    start_glue_crawler,
    update_dataset,
)
from integration_tests.modules.datasets_base.queries import list_datasets
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_ready
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_list_datasets(
    client1, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client1, term=session_id).nodes).is_length(3)


def test_list_datasets_unauthorized(
    client2, session_s3_dataset1, session_imported_sse_s3_dataset1, session_imported_kms_s3_dataset1, session_id
):
    assert_that(list_datasets(client2, term=session_id).nodes).is_length(0)


def test_list_owned_datasets():
    # TODO
    pass


def test_list_owned_datasets_unauthorized():
    # TODO
    pass


def test_list_datasets_created_in_environment():
    # TODO
    pass


def test_list_datasets_created_in_environment_unauthorized():
    # TODO
    pass
