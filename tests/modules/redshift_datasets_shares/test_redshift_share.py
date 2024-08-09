import pytest
from assertpy import assert_that


def test_create_redshift_share(redshift_share_request_1):
    assert redshift_share_request_1
