import pytest
from assertpy import assert_that


def test_approve_redshift_share(redshift_processor, mock_redshift_data_shares):
    # When
    response = redshift_processor.process_approved_shares()
    # Then
    assert_that(response).is_true()


def test_revoke_redshift_share(redshift_processor, mock_redshift_data_shares):
    # When
    response = redshift_processor.process_approved_shares()
    # Then
    assert_that(response).is_true()


def test_verify_redshift_share(redshift_processor, mock_redshift_data_shares):
    pass
