from assertpy import assert_that
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.modules.redshift_datasets_shares.services.redshift_table_share_validator import RedshiftTableValidator


def test_redshift_validator_create(
    db,
    user2,
    dataset_1,
    group2,
    env_fixture_2,
    target_connection_admin,
    mock_redshift_data_shares,
    source_connection_admin,
):
    # Given
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        set_context(RequestContext(db_engine=db, username=user2.username, groups=[group2.name], user_id=user2.username))
        response = validator.validate_share_object_create(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group2.name,
            principal_id=target_connection_admin.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        )
        dispose_context()
        # Then
        assert_that(response).is_true()
        mock_redshift_data_shares.return_value.check_redshift_role_in_namespace.assert_called_with(role='rs_role_1')


def test_redshift_validator_not_admin_target_connection(
    db, dataset_1, group2, env_fixture_2, target_connection_data_user, mock_redshift_data_shares, api_context_2
):
    # Given
    # A target connection of type DATA_USER
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        # Then because it is a DATA_USER connection no user has permissions to CREATE_SHARE_REQUEST (even the admins)
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group2.name,
            principal_id=target_connection_data_user.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        ).contains(
            'UnauthorizedOperation', 'CREATE_SHARE_REQUEST_WITH_CONNECTION', target_connection_data_user.connectionUri
        )


def test_redshift_validator_no_permissions_to_admin_connection(
    db, dataset_1, group3, env_fixture_2, target_connection_admin, mock_redshift_data_shares, api_context_3
):
    # Given user in another team without permissions to create request for this target connection
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        # Then
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group3.name,
            principal_id=target_connection_admin.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        ).contains(
            'UnauthorizedOperation', 'CREATE_SHARE_REQUEST_WITH_CONNECTION', target_connection_admin.connectionUri
        )


def test_redshift_validator_not_admin_source_connection(
    db, dataset_1, group2, env_fixture_2, target_connection_admin, mock_redshift_data_shares, api_context_2
):
    # Given
    validator = RedshiftTableValidator()
    # Since fixture source_connection_admin is not used, an ADMIN connection does not exist for dataset_1
    # When
    with db.scoped_session() as session:
        # Then
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group2.name,
            principal_id=target_connection_admin.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        ).contains('InvalidConfiguration', 'CREATE_SHARE_OBJECT', 'datashares require an ADMIN connection')


def test_redshift_validator_create_same_clusters(
    db, dataset_1, group, env_fixture, source_connection_admin, api_context_1
):
    # Given
    # that the target is the source_connection_admin = same namespace as source_connection_data_user
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        # Then
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture,
            group_uri=group.name,
            principal_id=source_connection_admin.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        ).contains('InvalidConfiguration', 'CREATE_SHARE_OBJECT', 'only possible between different namespaces')


def test_redshift_validator_role_does_not_exist(
    db,
    dataset_1,
    source_connection_admin,
    group2,
    env_fixture_2,
    target_connection_admin,
    mock_redshift_data_shares,
    api_context_2,
):
    # Given
    validator = RedshiftTableValidator()
    # When
    mock_redshift_data_shares.return_value.check_redshift_role_in_namespace.return_value = False
    with db.scoped_session() as session:
        # Then
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group2.name,
            principal_id=target_connection_admin.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
            permissions=[],
        ).contains('PrincipalRoleNotFound', 'CREATE_SHARE_OBJECT', 'Redshift role rs_role_1 does not exist')
