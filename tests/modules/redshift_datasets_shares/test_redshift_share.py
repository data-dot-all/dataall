from assertpy import assert_that


def test_create_redshift_share(redshift_share_request_cross_account, target_connection_admin, dataset_1):
    # Given redshift_share_request_1
    # When
    assert_that(redshift_share_request_cross_account).is_not_none()
    assert_that(redshift_share_request_cross_account.principalId).is_equal_to(target_connection_admin.connectionUri)
    assert_that(redshift_share_request_cross_account.principalRoleName).is_equal_to('rs_role_1')
    assert_that(redshift_share_request_cross_account.principalType).is_equal_to('Redshift_Role')
