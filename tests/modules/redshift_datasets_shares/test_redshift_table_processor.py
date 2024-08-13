from unittest.mock import call
from assertpy import assert_that
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.shares_enums import ShareItemHealthStatus


def test_approve_redshift_share_all_mocked(dataset_1, table1, redshift_processor, mock_redshift_data_shares):
    # When
    response = redshift_processor.process_approved_shares()
    # Then
    assert_that(response).is_true()
    mock_redshift_data_shares.return_value.create_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name
    )
    mock_redshift_data_shares.return_value.add_schema_to_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name, schema=dataset_1.schema
    )
    mock_redshift_data_shares.return_value.grant_usage_to_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name, namespace=redshift_processor.target_connection.nameSpaceId
    )
    mock_redshift_data_shares.return_value.drop_database.assert_called_with(
        database=redshift_processor._build_local_db_name()
    )
    mock_redshift_data_shares.return_value.create_database_from_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name,
        database=redshift_processor._build_local_db_name(),
        namespace=redshift_processor.source_connection.nameSpaceId,
    )
    mock_redshift_data_shares.return_value.grant_database_usage_access_to_redshift_role.assert_called_with(
        database=redshift_processor._build_local_db_name(), rs_role=redshift_processor.redshift_role
    )
    mock_redshift_data_shares.return_value.create_external_schema.assert_called_with(
        database=redshift_processor._build_local_db_name(),
        schema=dataset_1.schema,
        external_schema=redshift_processor._build_external_schema_name(),
    )

    mock_redshift_data_shares.return_value.grant_schema_usage_access_to_redshift_role.assert_has_calls(
        [
            call(schema=redshift_processor._build_external_schema_name(), rs_role=redshift_processor.redshift_role),
            call(
                database=redshift_processor._build_local_db_name(),
                schema=dataset_1.schema,
                rs_role=redshift_processor.redshift_role,
            ),
        ]
    )
    mock_redshift_data_shares.return_value.add_table_to_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name, schema=dataset_1.schema, table_name=table1.name
    )
    mock_redshift_data_shares.return_value.grant_select_table_access_to_redshift_role.assert_has_calls(
        [
            call(
                database=redshift_processor._build_local_db_name(),
                schema=dataset_1.schema,
                table=table1.name,
                rs_role=redshift_processor.redshift_role,
            ),
            call(
                schema=redshift_processor._build_external_schema_name(),
                table=table1.name,
                rs_role=redshift_processor.redshift_role,
            ),
        ]
    )


def test_revoke_redshift_share_all_mocked(dataset_1, table1, redshift_processor, mock_redshift_data_shares):
    # When
    response = redshift_processor.process_revoked_shares()
    # Then
    assert_that(response).is_true()
    mock_redshift_data_shares.return_value.check_database_exists.assert_called_with(
        database=redshift_processor._build_local_db_name()
    )
    mock_redshift_data_shares.return_value.check_schema_exists.assert_called_with(
        schema=redshift_processor._build_external_schema_name(), database=redshift_processor.target_connection.database
    )

    mock_redshift_data_shares.return_value.revoke_select_table_access_to_redshift_role.assert_has_calls(
        [
            call(
                schema=redshift_processor._build_external_schema_name(),
                table=table1.name,
                rs_role=redshift_processor.redshift_role,
            ),
            call(
                database=redshift_processor._build_local_db_name(),
                schema=dataset_1.schema,
                table=table1.name,
                rs_role=redshift_processor.redshift_role,
            ),
        ]
    )
    mock_redshift_data_shares.return_value.check_datashare_exists.assert_called_with(
        datashare=redshift_processor.datashare_name
    )
    mock_redshift_data_shares.return_value.remove_table_from_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name, schema=dataset_1.schema, table_name=table1.name
    )
    mock_redshift_data_shares.return_value.revoke_schema_usage_access_to_redshift_role(
        schema=redshift_processor._build_external_schema_name(), rs_role=redshift_processor.redshift_role
    )
    mock_redshift_data_shares.return_value.revoke_database_usage_access_to_redshift_role(
        database=redshift_processor._build_local_db_name(), rs_role=redshift_processor.redshift_role
    )
    mock_redshift_data_shares.return_value.drop_database.assert_called_with(
        database=redshift_processor._build_local_db_name()
    )
    mock_redshift_data_shares.return_value.drop_datashare(redshift_processor.datashare_name)


def test_verify_redshift_share_all_successful(dataset_1, table1, redshift_processor, mock_redshift_data_shares):
    # When
    response = redshift_processor.verify_shares()
    # Then
    assert_that(response).is_true()
    mock_redshift_data_shares.return_value.check_datashare_exists.assert_called_with(
        datashare=redshift_processor.datashare_name
    )
    mock_redshift_data_shares.return_value.check_schema_in_datashare.assert_called_with(
        schema=dataset_1.schema, datashare=redshift_processor.datashare_name
    )
    mock_redshift_data_shares.return_value.check_consumer_permissions_to_datashare(
        datashare=redshift_processor.datashare_name
    )
    mock_redshift_data_shares.return_value.check_database_exists.assert_called_with(
        database=redshift_processor._build_local_db_name()
    )
    mock_redshift_data_shares.return_value.check_role_permissions_in_database.assert_called_with(
        database=redshift_processor._build_local_db_name(), rs_role=redshift_processor.redshift_role
    )
    mock_redshift_data_shares.return_value.check_schema_exists.assert_called_with(
        schema=redshift_processor._build_external_schema_name(), database=redshift_processor.target_connection.database
    )
    mock_redshift_data_shares.return_value.check_role_permissions_in_schema.assert_called_with(
        schema=redshift_processor._build_external_schema_name(), rs_role=redshift_processor.redshift_role
    )
    mock_redshift_data_shares.return_value.check_table_in_datashare.assert_called_with(
        datashare=redshift_processor.datashare_name, table_name=table1.name
    )


def test_verify_redshift_share_datashare_does_not_exist(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_datashare_exists.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('Redshift datashare Target Resource does not exist')


def test_verify_redshift_schema_not_added_to_datashare(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_schema_in_datashare.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('Redshift schema added to datashare Target Resource does not exist')


def test_verify_consumer_permissions_to_datashare(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_consumer_permissions_to_datashare.return_value = False
    # When
    response = redshift_processor.verify_shares()
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('missing SHARE permissions: SHARE for Redshift datashare Target')


def test_verify_redshift_share_database_does_not_exist(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_database_exists.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('Redshift local database in consumer Target Resource does not exist')


def test_verify_role_permissions_to_database(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_role_permissions_in_database.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains(
            'missing USAGE permissions: USAGE for Redshift local database in consumer'
        )


def test_verify_external_schema_exists(db, redshift_requested_table, redshift_processor, mock_redshift_data_shares):
    # Given
    mock_redshift_data_shares.return_value.check_schema_exists.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('Redshift external schema Target Resource does not exist')


def test_verify_role_permissions_to_schema(db, redshift_requested_table, redshift_processor, mock_redshift_data_shares):
    # Given
    mock_redshift_data_shares.return_value.check_role_permissions_in_schema.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('missing USAGE permissions: USAGE for Redshift external schema')


def test_verify_table_not_added_to_datashare(
    db, redshift_requested_table, redshift_processor, mock_redshift_data_shares
):
    # Given
    mock_redshift_data_shares.return_value.check_table_in_datashare.return_value = False
    # When
    response = redshift_processor.verify_shares()
    # Then
    with db.scoped_session() as session:
        item = ShareObjectRepository.get_share_item_by_uri(session, redshift_requested_table.shareItemUri)
        assert_that(item.healthStatus).is_equal_to(ShareItemHealthStatus.Unhealthy.value)
        assert_that(item.healthMessage).contains('Redshift table added to datashare Target Resource does not exist')
