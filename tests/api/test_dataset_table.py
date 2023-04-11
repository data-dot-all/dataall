import typing

import pytest

import dataall
from dataall.modules.datasets.services.dataset_table import DatasetTableService


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset1(env1, org1, dataset, group) -> dataall.db.models.Dataset:
    yield dataset(
        org=org1, env=env1, name='dataset1', owner=env1.owner, group=group.name
    )


@pytest.fixture(scope='module')
def org2(org: typing.Callable, user2, group2, tenant) -> dataall.db.models.Organization:
    yield org('org2', user2.userName, group2.name)


@pytest.fixture(scope='module')
def env2(
    env: typing.Callable, org2: dataall.db.models.Organization, user2, group2, tenant
) -> dataall.db.models.Environment:
    yield env(org2, 'dev', user2.userName, group2.name, '2' * 12, 'eu-west-2')


def test_init(db):
    assert True


def test_get_dataset(client, dataset1, env1, user):
    response = client.query(
        """
        query GetDataset($datasetUri:String!){
            getDataset(datasetUri:$datasetUri){
                label
                AwsAccountId
                description
                region
                imported
                importedS3Bucket
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username=user.userName,
        groups=[dataset1.SamlAdminGroupName],
    )
    assert response.data.getDataset.AwsAccountId == env1.AwsAccountId
    assert response.data.getDataset.region == env1.region
    assert response.data.getDataset.label == 'dataset1'
    assert response.data.getDataset.imported is False
    assert response.data.getDataset.importedS3Bucket is False


def test_add_tables(table, dataset1, db):
    for i in range(0, 10):
        table(dataset=dataset1, name=f'table{i+1}', username=dataset1.owner)

    with db.scoped_session() as session:
        nb = session.query(dataall.db.models.DatasetTable).count()
    assert nb == 10


def test_update_table(client, env1, table, dataset1, db, user, group):
    table_to_update = table(
        dataset=dataset1, name=f'table_to_update', username=dataset1.owner
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
        username=user.userName,
        groups=[group.name],
        tableUri=table_to_update.tableUri,
        input={
            'description': 'test update',
            'tags': ['t1', 't2'],
        },
    )
    assert response.data.updateDatasetTable.description == 'test update'
    assert 't1' in response.data.updateDatasetTable.tags


def test_add_columns(table, dataset1, db):
    with db.scoped_session() as session:
        table = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'table1')
            .first()
        )
        table_col = dataall.db.models.DatasetTableColumn(
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


def test_list_dataset_tables(client, dataset1):
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
        username=dataset1.owner,
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 100},
        groups=[dataset1.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count >= 10
    assert len(response.data.getDataset.tables.nodes) >= 10

    response = client.query(
        q,
        username=dataset1.owner,
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 3},
        groups=[dataset1.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count >= 10
    assert len(response.data.getDataset.tables.nodes) == 3

    response = client.query(
        q,
        username=dataset1.owner,
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 100, 'term': 'table1'},
        groups=[dataset1.SamlAdminGroupName],
    )
    assert response.data.getDataset.tables.count == 2
    assert len(response.data.getDataset.tables.nodes) == 2


def test_update_dataset_table_column(client, table, dataset1, db):
    with db.scoped_session() as session:
        table = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'table1')
            .first()
        )
        column = (
            session.query(dataall.db.models.DatasetTableColumn)
            .filter(dataall.db.models.DatasetTableColumn.tableUri == table.tableUri)
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
            username=dataset1.owner,
            columnUri=column.columnUri,
            input={'description': 'My new description'},
            groups=[dataset1.SamlAdminGroupName],
        )
        print('response', response)
        assert (
            response.data.updateDatasetTableColumn.description == 'My new description'
        )

        column = session.query(dataall.db.models.DatasetTableColumn).get(
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


def test_sync_tables_and_columns(client, table, dataset1, db):
    with db.scoped_session() as session:
        table = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'table1')
            .first()
        )
        column = (
            session.query(dataall.db.models.DatasetTableColumn)
            .filter(dataall.db.models.DatasetTableColumn.tableUri == table.tableUri)
            .first()
        )
        glue_tables = [
            {
                'Name': 'new_table',
                'DatabaseName': dataset1.GlueDatabaseName,
                'StorageDescriptor': {
                    'Columns': [
                        {
                            'Name': 'col1',
                            'Type': 'string',
                            'Comment': 'comment_col',
                            'Parameters': {'colp1': 'p1'},
                        },
                    ],
                    'Location': f's3://{dataset1.S3BucketName}/table1',
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
                'DatabaseName': dataset1.GlueDatabaseName,
                'StorageDescriptor': {
                    'Columns': [
                        {
                            'Name': 'col1',
                            'Type': 'string',
                            'Comment': 'comment_col',
                            'Parameters': {'colp1': 'p1'},
                        },
                    ],
                    'Location': f's3://{dataset1.S3BucketName}/table1',
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

        assert DatasetTableService.sync(session, dataset1.datasetUri, glue_tables)
        new_table: dataall.db.models.DatasetTable = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'new_table')
            .first()
        )
        assert new_table
        assert new_table.GlueTableName == 'new_table'
        columns: [dataall.db.models.DatasetTableColumn] = (
            session.query(dataall.db.models.DatasetTableColumn)
            .filter(dataall.db.models.DatasetTableColumn.tableUri == new_table.tableUri)
            .order_by(dataall.db.models.DatasetTableColumn.columnType.asc())
            .all()
        )
        assert len(columns) == 2
        assert columns[0].columnType == 'column'
        assert columns[1].columnType == 'partition_0'

        existing_table: dataall.db.models.DatasetTable = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'table1')
            .first()
        )
        assert existing_table
        assert existing_table.GlueTableName == 'table1'
        columns: [dataall.db.models.DatasetTableColumn] = (
            session.query(dataall.db.models.DatasetTableColumn)
            .filter(dataall.db.models.DatasetTableColumn.tableUri == new_table.tableUri)
            .order_by(dataall.db.models.DatasetTableColumn.columnType.asc())
            .all()
        )
        assert len(columns) == 2
        assert columns[0].columnType == 'column'
        assert columns[1].columnType == 'partition_0'

        deleted_table: dataall.db.models.DatasetTable = (
            session.query(dataall.db.models.DatasetTable)
            .filter(dataall.db.models.DatasetTable.name == 'table2')
            .first()
        )
        assert deleted_table.LastGlueTableStatus == 'Deleted'


def test_delete_table(client, table, dataset1, db, group):
    table_to_delete = table(
        dataset=dataset1, name=f'table_to_update', username=dataset1.owner
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
