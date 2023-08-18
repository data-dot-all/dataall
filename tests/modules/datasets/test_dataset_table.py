from dataall.modules.datasets.services.dataset_table_service import DatasetTableService
from dataall.modules.datasets_base.db.models import DatasetTableColumn, DatasetTable, Dataset


def test_add_tables(table, dataset_fixture, db):
    for i in range(0, 10):
        table(dataset=dataset_fixture, name=f'table{i+1}', username=dataset_fixture.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetTable).count()
    assert nb == 10


def test_update_table(client, table, dataset_fixture, db, user, group):
    table_to_update = table(
        dataset=dataset_fixture, name=f'table_to_update', username=dataset_fixture.owner
    )
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
        table = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'table1')
            .first()
        )
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
                        GlueDatabaseName
                        GlueTableName
                        S3Prefix
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
        table = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'table1')
            .first()
        )
        column = (
            session.query(DatasetTableColumn)
            .filter(DatasetTableColumn.tableUri == table.tableUri)
            .first()
        )
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
        assert (
            response.data.updateDatasetTableColumn.description == 'My new description'
        )

        column = session.query(DatasetTableColumn).get(
            column.columnUri
        )
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
        table = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'table1')
            .first()
        )
        column = (
            session.query(DatasetTableColumn)
            .filter(DatasetTableColumn.tableUri == table.tableUri)
            .first()
        )
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

        assert DatasetTableService.sync_existing_tables(session, dataset_fixture.datasetUri, glue_tables)
        new_table: DatasetTable = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'new_table')
            .first()
        )
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

        existing_table: DatasetTable = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'table1')
            .first()
        )
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

        deleted_table: DatasetTable = (
            session.query(DatasetTable)
            .filter(DatasetTable.name == 'table2')
            .first()
        )
        assert deleted_table.LastGlueTableStatus == 'Deleted'


def test_delete_table(client, table, dataset_fixture, db, group):
    table_to_delete = table(
        dataset=dataset_fixture, name=f'table_to_update', username=dataset_fixture.owner
    )
    response = client.query(
        """
        mutation deleteDatasetTable($tableUri:String!){
                deleteDatasetTable(tableUri:$tableUri)
            }
        """,
        username='alice',
        groups=[group.name],
        tableUri=table_to_delete.tableUri,
    )
    assert response.data.deleteDatasetTable
