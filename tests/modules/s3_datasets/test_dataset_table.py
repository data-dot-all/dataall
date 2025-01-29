from dataall.modules.s3_datasets.services.dataset_table_service import DatasetTableService
from dataall.modules.s3_datasets.services.dataset_table_data_filter_service import DatasetTableDataFilterService
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableColumn, DatasetTable, DatasetTableDataFilter
from dataall.base.db.exceptions import UnauthorizedOperation
import pytest
import boto3
from unittest.mock import MagicMock


@pytest.fixture(scope='function')
def mock_lf_client(mocker, mock_aws_client):
    mocker.patch('dataall.modules.s3_datasets.aws.lf_data_filter_client.SessionHelper', autospec=True)

    mock_class = mocker.patch(
        'dataall.modules.s3_datasets.aws.lf_data_filter_client.LakeFormationDataFilterClient', autospec=True
    )

    mock_class._create_table_data_filter.return_value = {}


def test_add_tables(table, dataset_fixture, db):
    for i in range(0, 10):
        table(dataset=dataset_fixture, name=f'table{i + 1}', username=dataset_fixture.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetTable).count()
    assert nb == 10


def test_update_table(client, table, dataset_fixture, db, user, group):
    table_to_update = table(dataset=dataset_fixture, name=f'table_to_update', username=dataset_fixture.owner)
    response = client.query(
        """
        mutation UpdateDatasetTable($tableUri:String!,$input:ModifyDatasetTableInput!){
                updateDatasetTable(tableUri:$tableUri,input:$input){
                    tableUri
                    description
                    tags
                }
            }
        """,
        username=user.username,
        groups=[group.name],
        tableUri=table_to_update.tableUri,
        input={
            'description': 'test update',
            'tags': ['t1', 't2'],
        },
    )
    assert response.data.updateDatasetTable.description == 'test update'
    assert 't1' in response.data.updateDatasetTable.tags


def test_add_columns(table, dataset_fixture, db):
    with db.scoped_session() as session:
        table = session.query(DatasetTable).filter(DatasetTable.name == 'table1').first()
        table_col = DatasetTableColumn(
            name='col1',
            description='None',
            label='col1',
            owner=table.owner,
            datasetUri=table.datasetUri,
            tableUri=table.tableUri,
            AWSAccountId=table.AWSAccountId,
            GlueDatabaseName=table.GlueDatabaseName,
            GlueTableName=table.GlueTableName,
            region=table.region,
            typeName='String',
        )
        session.add(table_col)


def test_list_dataset_tables(client, dataset_fixture):
    q = """
        query GetDataset($datasetUri:String!,$tableFilter:DatasetTableFilter){
            getDataset(datasetUri:$datasetUri){
                datasetUri
                tables(filter:$tableFilter){
                    count
                    nodes{
                        tableUri
                        name
                        label
                        restricted {
                            GlueDatabaseName
                            GlueTableName
                            S3Prefix
                        }
                    }
                }
            }
        }
    """
    response = client.query(
        q,
        username=dataset_fixture.owner,
        datasetUri=dataset_fixture.datasetUri,
        tableFilter={'pageSize': 100},
        groups=[dataset_fixture.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count >= 10
    assert len(response.data.getDataset.tables.nodes) >= 10

    response = client.query(
        q,
        username=dataset_fixture.owner,
        datasetUri=dataset_fixture.datasetUri,
        tableFilter={'pageSize': 3},
        groups=[dataset_fixture.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count >= 10
    assert len(response.data.getDataset.tables.nodes) == 3

    response = client.query(
        q,
        username=dataset_fixture.owner,
        datasetUri=dataset_fixture.datasetUri,
        tableFilter={'pageSize': 100, 'term': 'table1'},
        groups=[dataset_fixture.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count == 2
    assert len(response.data.getDataset.tables.nodes) == 2


def test_update_dataset_table_column(client, table, dataset_fixture, db):
    with db.scoped_session() as session:
        table = session.query(DatasetTable).filter(DatasetTable.name == 'table1').first()
        column = session.query(DatasetTableColumn).filter(DatasetTableColumn.tableUri == table.tableUri).first()
        response = client.query(
            """
            mutation updateDatasetTableColumn($columnUri:String!,$input:DatasetTableColumnInput){
                updateDatasetTableColumn(columnUri:$columnUri,input:$input){
                    description
                }
            }
            """,
            username=dataset_fixture.owner,
            columnUri=column.columnUri,
            input={'description': 'My new description'},
            groups=[dataset_fixture.SamlAdminGroupName],
        )
        print('response', response)
        assert response.data.updateDatasetTableColumn.description == 'My new description'

        column = session.query(DatasetTableColumn).get(column.columnUri)
        assert column.description == 'My new description'
        response = client.query(
            """
            mutation updateDatasetTableColumn($columnUri:String!,$input:DatasetTableColumnInput){
                updateDatasetTableColumn(columnUri:$columnUri,input:$input){
                    description
                }
            }
            """,
            username='unauthorized',
            columnUri=column.columnUri,
            input={'description': 'My new description'},
        )
        assert 'Unauthorized' in response.errors[0].message


def test_sync_tables_and_columns(client, table, dataset_fixture, db):
    with db.scoped_session() as session:
        table = session.query(DatasetTable).filter(DatasetTable.name == 'table1').first()
        column = session.query(DatasetTableColumn).filter(DatasetTableColumn.tableUri == table.tableUri).first()
        glue_tables = [
            {
                'Name': 'new_table',
                'DatabaseName': dataset_fixture.GlueDatabaseName,
                'StorageDescriptor': {
                    'Columns': [
                        {
                            'Name': 'col1',
                            'Type': 'string',
                            'Comment': 'comment_col',
                            'Parameters': {'colp1': 'p1'},
                        },
                    ],
                    'Location': f's3://{dataset_fixture.S3BucketName}/table1',
                    'Parameters': {'p1': 'p1'},
                },
                'PartitionKeys': [
                    {
                        'Name': 'partition1',
                        'Type': 'string',
                        'Comment': 'comment_partition',
                        'Parameters': {'partition_1': 'p1'},
                    },
                ],
            },
            {
                'Name': 'table1',
                'DatabaseName': dataset_fixture.GlueDatabaseName,
                'StorageDescriptor': {
                    'Columns': [
                        {
                            'Name': 'col1',
                            'Type': 'string',
                            'Comment': 'comment_col',
                            'Parameters': {'colp1': 'p1'},
                        },
                    ],
                    'Location': f's3://{dataset_fixture.S3BucketName}/table1',
                    'Parameters': {'p1': 'p1'},
                },
                'PartitionKeys': [
                    {
                        'Name': 'partition1',
                        'Type': 'string',
                        'Comment': 'comment_partition',
                        'Parameters': {'partition_1': 'p1'},
                    },
                ],
            },
        ]

        assert DatasetTableService.sync_existing_tables(
            session, uri=dataset_fixture.datasetUri, glue_tables=glue_tables
        )
        new_table: DatasetTable = session.query(DatasetTable).filter(DatasetTable.name == 'new_table').first()
        assert new_table
        assert new_table.GlueTableName == 'new_table'
        columns: [DatasetTableColumn] = (
            session.query(DatasetTableColumn)
            .filter(DatasetTableColumn.tableUri == new_table.tableUri)
            .order_by(DatasetTableColumn.columnType.asc())
            .all()
        )
        assert len(columns) == 2
        assert columns[0].columnType == 'column'
        assert columns[1].columnType == 'partition_0'

        existing_table: DatasetTable = session.query(DatasetTable).filter(DatasetTable.name == 'table1').first()
        assert existing_table
        assert existing_table.GlueTableName == 'table1'
        columns: [DatasetTableColumn] = (
            session.query(DatasetTableColumn)
            .filter(DatasetTableColumn.tableUri == new_table.tableUri)
            .order_by(DatasetTableColumn.columnType.asc())
            .all()
        )
        assert len(columns) == 2
        assert columns[0].columnType == 'column'
        assert columns[1].columnType == 'partition_0'

        deleted_table: DatasetTable = session.query(DatasetTable).filter(DatasetTable.name == 'table2').first()
        assert deleted_table.LastGlueTableStatus == 'Deleted'


def delete_table(client, tableUri, username, groups):
    return client.query(
        """
        mutation deleteDatasetTable($tableUri:String!){
                deleteDatasetTable(tableUri:$tableUri)
            }
        """,
        username=username,
        groups=groups,
        tableUri=tableUri,
    )


def test_delete_table(mock_lf_client, client, table, dataset_fixture, db, group):
    table_to_delete = table(dataset=dataset_fixture, name=f'table_to_update', username=dataset_fixture.owner)
    response = delete_table(client, table_to_delete.tableUri, 'alice', [group.name])
    assert response.data.deleteDatasetTable


def create_data_filter(client, tableUri, username, groups, input):
    return client.query(
        """
        mutation createTableDataFilter($tableUri: String!,$input: NewTableDataFilterInput!) {
            createTableDataFilter(tableUri: $tableUri, input: $input) {
                filterUri
                label
                description
                filterType
                includedCols
            }
        }
        """,
        tableUri=tableUri,
        groups=groups,
        username=username,
        input=input,
    )


def list_data_filters(client, tableUri, username, groups):
    return client.query(
        """
        query listTableDataFilters(
          $tableUri: String!
          $filter: DatasetTableFilter
        ) {
          listTableDataFilters(tableUri: $tableUri, filter: $filter) {
            count
            page
            pages
            hasNext
            hasPrevious
            nodes {
              filterUri
              label
              description
              filterType
              includedCols
              rowExpression
            }
          }
        }
        """,
        tableUri=tableUri,
        groups=groups,
        username=username,
    )


def delete_data_filters(client, filterUri, username, groups):
    return client.query(
        """
        mutation deleteTableDataFilter($filterUri: String!) {
            deleteTableDataFilter(filterUri: $filterUri)
        }
        """,
        filterUri=filterUri,
        groups=groups,
        username=username,
    )


def test_delete_table_with_filters(mock_lf_client, client, table, dataset_fixture, db, user, group):
    table_to_delete = table(dataset=dataset_fixture, name='table', username=dataset_fixture.owner)

    filterName = 'colfilter'
    filterType = 'COLUMN'
    input = {
        'filterName': filterName,
        'filterType': filterType,
        'includedCols': ['id'],
    }
    create_data_filter(client, table_to_delete.tableUri, user.username, [group.name], input)

    dfilter_response = list_data_filters(client, table_to_delete.tableUri, user.username, [group.name])
    assert dfilter_response.data.listTableDataFilters.count == 1

    response = delete_table(client, table_to_delete.tableUri, user.username, [group.name])

    dfilter_response = list_data_filters(client, table_to_delete.tableUri, user.username, [group.name])
    assert 'UnauthorizedOperation' in dfilter_response.errors[0].message
    with db.scoped_session() as session:
        assert (
            session.query(DatasetTableDataFilter)
            .filter(DatasetTableDataFilter.tableUri == table_to_delete.tableUri)
            .count()
            == 0
        )


def test_create_table_data_filter_column(mock_lf_client, client, table_fixture, db, user, group):
    filterName = 'colfilter'
    filterType = 'COLUMN'
    input = {
        'filterName': filterName,
        'description': 'mylocation',
        'filterType': filterType,
        'rowExpression': '',
        'includedCols': ['id_col', 'id2_col'],
    }
    response = create_data_filter(client, table_fixture.tableUri, user.username, [group.name], input)

    assert response.data.createTableDataFilter
    assert response.data.createTableDataFilter.filterUri
    assert response.data.createTableDataFilter.label == filterName
    assert response.data.createTableDataFilter.filterType == filterType
    assert response.data.createTableDataFilter.rowExpression is None


def test_create_table_data_filter_row(mock_lf_client, client, table_fixture, db, user, group):
    filterName = 'rowfilter'
    filterType = 'ROW'
    input = {
        'filterName': filterName,
        'description': 'mylocation',
        'filterType': filterType,
        'rowExpression': 'id_col IS NOT NULL AND id2_col > 100',
        'includedCols': [],
    }
    response = create_data_filter(client, table_fixture.tableUri, user.username, [group.name], input)

    assert response.data.createTableDataFilter
    assert response.data.createTableDataFilter.filterUri
    assert response.data.createTableDataFilter.label == filterName
    assert response.data.createTableDataFilter.filterType == filterType
    assert response.data.createTableDataFilter.includedCols is None


def test_create_table_data_filter_invalid_input(mock_lf_client, client, table_fixture, db, user, group):
    filterName = 'RowFilter ###'
    filterType = 'ROW'
    input = {
        'filterName': filterName,
        'description': 'mylocation',
        'filterType': filterType,
        'rowExpression': 'id_col IS NOT NULL AND id2_col > 100',
        'includedCols': [],
    }

    response = create_data_filter(client, table_fixture.tableUri, user.username, [group.name], input)

    assert response.errors
    assert 'InvalidInput' in response.errors[0].message


def test_create_table_data_filter_invalid_type(mock_lf_client, client, table_fixture, db, user, group):
    filterName = 'filter'
    filterType = 'NEWTYPE'
    input = {
        'filterName': filterName,
        'description': 'mylocation',
        'filterType': filterType,
        'rowExpression': 'id_col IS NOT NULL AND id2_col > 100',
        'includedCols': [],
    }

    response = create_data_filter(client, table_fixture.tableUri, user.username, [group.name], input)

    assert response.errors
    assert 'InvalidInput' in response.errors[0].message


def test_list_table_data_filters(mock_lf_client, client, table_fixture, db, user, group):
    response = list_data_filters(client, table_fixture.tableUri, user.username, [group.name])

    assert response.data.listTableDataFilters.count == 2
    for dfilter in response.data.listTableDataFilters.nodes:
        assert dfilter.filterType in ['COLUMN', 'ROW']


def test_delete_table_data_filter(mock_lf_client, client, table_fixture, db, user, group):
    response = list_data_filters(client, table_fixture.tableUri, user.username, [group.name])
    for dfilter in response.data.listTableDataFilters.nodes:
        response = delete_data_filters(client, dfilter.filterUri, user.username, [group.name])
