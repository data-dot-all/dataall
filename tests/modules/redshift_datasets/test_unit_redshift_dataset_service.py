from assertpy import assert_that
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService


def test_import_redshift_dataset_with_no_tables(imported_redshift_dataset_1_no_tables, api_context_1):
    # When dataset is imported
    # Then
    assert_that(imported_redshift_dataset_1_no_tables).is_not_none()
    assert_that(imported_redshift_dataset_1_no_tables.datasetUri).is_not_none()
    assert_that(imported_redshift_dataset_1_no_tables.schema).is_equal_to('public')
    # When we list the tables in this dataset
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, filter={}
    )
    # Then
    assert_that(tables).contains_entry(count=0)


def test_import_redshift_dataset_with_tables(imported_redshift_dataset_2_with_tables, api_context_1):
    # When dataset is imported
    # Then
    assert_that(imported_redshift_dataset_2_with_tables).is_not_none()
    assert_that(imported_redshift_dataset_2_with_tables.datasetUri).is_not_none()
    assert_that(imported_redshift_dataset_2_with_tables.schema).is_equal_to('public')
    # When we list the tables in this dataset
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_2_with_tables.datasetUri, filter={}
    )
    # Then
    assert_that(tables).contains_entry(count=2)


def test_update_redshift_dataset_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.update_redshift_dataset).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, data={'description': 'new description'}
    ).contains('UnauthorizedOperation', 'UPDATE_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_update_redshift_dataset(imported_redshift_dataset_1_no_tables, group3, group, api_context_1):
    # When
    dataset = RedshiftDatasetService.update_redshift_dataset(
        uri=imported_redshift_dataset_1_no_tables.datasetUri,
        data={'description': 'new description', 'stewards': group3.name},
    )
    # Then
    assert_that(dataset.description).is_equal_to('new description')
    assert_that(dataset.stewards).is_equal_to(group3.name)
    # Revert stewards
    dataset = RedshiftDatasetService.update_redshift_dataset(
        uri=imported_redshift_dataset_1_no_tables.datasetUri,
        data={'description': 'new description', 'stewards': group.name},
    )
    assert_that(dataset.stewards).is_equal_to(group.name)


def test_delete_redshift_dataset_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.delete_redshift_dataset).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri,
    ).contains('UnauthorizedOperation', 'DELETE_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_delete_redshift_dataset(env_fixture, group, connection1_serverless, api_context_1, mock_redshift_data):
    dataset = RedshiftDatasetService.import_redshift_dataset(
        uri=env_fixture.environmentUri,
        admin_group=group.name,
        data={
            'label': 'imported_redshift_to_delete',
            'SamlAdminGroupName': group.name,
            'connectionUri': connection1_serverless.connectionUri,
            'schema': 'public',
        },
    )
    # When
    response = RedshiftDatasetService.delete_redshift_dataset(
        uri=dataset.datasetUri,
    )
    # Then
    assert_that(response).is_true()


def test_add_redshift_dataset_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.add_redshift_dataset_tables).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, tables=['table3']
    ).contains('UnauthorizedOperation', 'ADD_TABLES_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_add_redshift_dataset_tables(imported_redshift_dataset_1_no_tables, api_context_1):
    # When
    response = RedshiftDatasetService.add_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, tables=['table3']
    )
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, filter={'term': 'table3'}
    )
    # Then
    assert_that(tables).contains_entry(count=1)


def test_add_redshift_dataset_tables_invalid_table(
    imported_redshift_dataset_1_no_tables, api_context_1, mock_redshift_data
):
    # When
    response = RedshiftDatasetService.add_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, tables=['table-does-not-exist']
    )
    assert_that(response.get('errorTables')).contains('table-does-not-exist')
    assert_that(response.get('successTables')).is_empty()


def test_delete_redshift_dataset_table_unauthorized(imported_dataset_2_table_1, api_context_2):
    # When
    assert_that(RedshiftDatasetService.delete_redshift_dataset_table).raises(Exception).when_called_with(
        uri=imported_dataset_2_table_1.rsTableUri
    ).contains('UnauthorizedOperation', 'DELETE_REDSHIFT_DATASET_TABLE', imported_dataset_2_table_1.rsTableUri)


def test_delete_redshift_dataset_table(imported_redshift_dataset_1_no_tables, api_context_1):
    # Given`
    response = RedshiftDatasetService.add_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, tables=['table4']
    )
    tables = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, filter={'term': 'table4'}
    )
    # When
    response = RedshiftDatasetService.delete_redshift_dataset_table(uri=tables['nodes'][0].rsTableUri)
    assert_that(response).is_true()


def test_update_redshift_dataset_table_unauthorized(imported_dataset_2_table_1, api_context_2):
    # When
    assert_that(RedshiftDatasetService.update_redshift_dataset_table).raises(Exception).when_called_with(
        uri=imported_dataset_2_table_1.rsTableUri, data={'description': 'new description'}
    ).contains('UnauthorizedOperation', 'UPDATE_REDSHIFT_DATASET_TABLE', imported_dataset_2_table_1.rsTableUri)


def test_update_redshift_dataset_table(imported_dataset_2_table_1, api_context_1):
    # When
    table = RedshiftDatasetService.update_redshift_dataset_table(
        uri=imported_dataset_2_table_1.rsTableUri, data={'description': 'new description'}
    )
    # Then
    assert_that(table.description).is_equal_to('new description')


def test_get_redshift_dataset_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.get_redshift_dataset).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_get_redshift_dataset(imported_redshift_dataset_1_no_tables, api_context_1):
    # When
    dataset = RedshiftDatasetService.get_redshift_dataset(uri=imported_redshift_dataset_1_no_tables.datasetUri)
    # Then
    assert_that(dataset.datasetUri).is_equal_to(imported_redshift_dataset_1_no_tables.datasetUri)
    assert_that(dataset.schema).is_equal_to('public')


def test_list_redshift_dataset_tables_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.list_redshift_dataset_tables).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri, filter={}
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_list_redshift_dataset_tables(imported_redshift_dataset_2_with_tables, api_context_1):
    # When
    response = RedshiftDatasetService.list_redshift_dataset_tables(
        uri=imported_redshift_dataset_2_with_tables.datasetUri, filter={}
    )
    # Then
    assert_that(response).contains_key('count', 'page', 'pages', 'nodes')


def test_list_redshift_schema_dataset_tables_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.list_redshift_schema_dataset_tables).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_list_redshift_schema_dataset_tables(imported_redshift_dataset_1_no_tables, mock_redshift, api_context_1):
    # When
    tables = RedshiftDatasetService.list_redshift_schema_dataset_tables(
        uri=imported_redshift_dataset_1_no_tables.datasetUri
    )
    # Then
    assert_that(tables).is_not_none()
    assert_that(tables[0]).contains_key('alreadyAdded', 'type', 'name')


def test_get_dataset_upvotes_unauthorized(imported_redshift_dataset_1_no_tables, api_context_2):
    # When
    assert_that(RedshiftDatasetService.get_dataset_upvotes).raises(Exception).when_called_with(
        uri=imported_redshift_dataset_1_no_tables.datasetUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET', imported_redshift_dataset_1_no_tables.datasetUri)


def test_get_dataset_upvotes(imported_redshift_dataset_1_no_tables, api_context_1):
    # When
    response = RedshiftDatasetService.get_dataset_upvotes(uri=imported_redshift_dataset_1_no_tables.datasetUri)
    # Then
    assert_that(response).is_equal_to(0)


def test_get_redshift_dataset_table_unauthorized(imported_dataset_2_table_1, api_context_2):
    # When
    assert_that(RedshiftDatasetService.get_redshift_dataset_table).raises(Exception).when_called_with(
        uri=imported_dataset_2_table_1.rsTableUri
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET_TABLE', imported_dataset_2_table_1.rsTableUri)


def test_get_redshift_dataset_table(imported_dataset_2_table_1, api_context_1):
    # When
    table = RedshiftDatasetService.get_redshift_dataset_table(uri=imported_dataset_2_table_1.rsTableUri)
    # Then
    assert_that(table.rsTableUri).is_equal_to(imported_dataset_2_table_1.rsTableUri)
    assert_that(table.name).is_equal_to('table1')


def test_list_redshift_dataset_table_columns_unauthorized(imported_dataset_2_table_1, api_context_2):
    # When
    assert_that(RedshiftDatasetService.list_redshift_dataset_table_columns).raises(Exception).when_called_with(
        uri=imported_dataset_2_table_1.rsTableUri, filter={}
    ).contains('UnauthorizedOperation', 'GET_REDSHIFT_DATASET_TABLE', imported_dataset_2_table_1.rsTableUri)


def test_list_redshift_dataset_table_columns(imported_dataset_2_table_1, api_context_1):
    # When
    response = RedshiftDatasetService.list_redshift_dataset_table_columns(
        uri=imported_dataset_2_table_1.rsTableUri, filter={}
    )
    # Then
    assert_that(response).contains_key('count', 'page', 'pages', 'nodes')
    assert_that(response['nodes']).is_length(4)
