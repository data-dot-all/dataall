import pytest
from assertpy import assert_that


def test_create_redshift_share(redshift_share_request_cross_account, target_connection, dataset_1):
    # Given redshift_share_request_1
    # When
    assert redshift_share_request_cross_account
    assert redshift_share_request_cross_account.principalId == target_connection.connectionUri
    assert redshift_share_request_cross_account.principalRoleName == 'rs_role_1'
    assert redshift_share_request_cross_account.principalType == 'Redshift_Role'
