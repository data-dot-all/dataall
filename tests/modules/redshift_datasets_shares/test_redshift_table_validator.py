from assertpy import assert_that
from dataall.modules.redshift_datasets_shares.services.redshift_table_share_validator import RedshiftTableValidator


def test_redshift_validator_create(
    db, dataset_1, group2, env_fixture_2, target_connection, mock_redshift_data_shares, source_connection_admin
):
    # Given
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        response = validator.validate_share_object_create(
            session=session,
            dataset=dataset_1,
            environment=env_fixture_2,
            group_uri=group2.name,
            principal_id=target_connection.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
        )
        # Then
        assert_that(response).is_true()
        mock_redshift_data_shares.return_value.check_redshift_role_in_namespace.assert_called_with(role='rs_role_1')


def test_redshift_validator_create_same_clusters(db, dataset_1, group, env_fixture, source_connection):
    # Given
    validator = RedshiftTableValidator()
    # When
    with db.scoped_session() as session:
        # Then
        assert_that(validator.validate_share_object_create).raises(Exception).when_called_with(
            session=session,
            dataset=dataset_1,
            environment=env_fixture,
            group_uri=group.name,
            principal_id=source_connection.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
        ).contains('InvalidConfiguration', 'CREATE_SHARE_OBJECT', 'only possible between different namespaces')


def test_redshift_validator_role_does_not_exist(
    db, dataset_1, group2, env_fixture_2, target_connection, mock_redshift_data_shares
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
            principal_id=target_connection.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
        ).contains('PrincipalRoleNotFound', 'CREATE_SHARE_OBJECT', 'Redshift role rs_role_1 does not exist')


def test_redshift_validator_not_admin_connection(
    db, dataset_1, group2, env_fixture_2, target_connection, mock_redshift_data_shares
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
            principal_id=target_connection.connectionUri,
            principal_role_name='rs_role_1',
            principal_type='Redshift_Role',
            attachMissingPolicies=False,
        ).contains('InvalidConfiguration', 'CREATE_SHARE_OBJECT', 'datashares require an ADMIN connection')
