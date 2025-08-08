import pytest
from unittest.mock import MagicMock

from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetStorageLocation


def test_list_dataset_tables_folders_basic(client, dataset_fixture, table, location):
    """Test basic listing of dataset tables and folders"""
    # Create some test tables and folders
    table1 = table(dataset=dataset_fixture, name='test_table_1', username=dataset_fixture.owner)
    table2 = table(dataset=dataset_fixture, name='test_table_2', username=dataset_fixture.owner)
    location1 = location(dataset=dataset_fixture, name='test_folder_1', username=dataset_fixture.owner)
    location2 = location(dataset=dataset_fixture, name='test_folder_2', username=dataset_fixture.owner)

    response = client.query(
        """
        query listDatasetTablesFolders(
            $datasetUri: String!,
            $filter: DatasetFilter
        ) {
            listDatasetTablesFolders(
                datasetUri: $datasetUri,
                filter: $filter
            ) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                    name
                    targetType
                    targetUri
                }
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        datasetUri=dataset_fixture.datasetUri,
        filter={},
    )

    assert not response.errors
    assert response.data.listDatasetTablesFolders.count >= 4  # At least our 2 tables + 2 folders

    # Check that we have both tables and folders in the results
    nodes = response.data.listDatasetTablesFolders.nodes
    table_nodes = [node for node in nodes if node.targetType == 'Table']
    folder_nodes = [node for node in nodes if node.targetType == 'Folder']

    assert len(table_nodes) >= 2
    assert len(folder_nodes) >= 2

    # Verify specific items are present
    table_names = [node.name for node in table_nodes]
    folder_names = [node.name for node in folder_nodes]

    assert 'test_table_1' in table_names
    assert 'test_table_2' in table_names
    assert 'test_folder_1' in folder_names
    assert 'test_folder_2' in folder_names


def test_list_dataset_tables_folders_with_pagination(client, dataset_fixture, table, location):
    """Test listing with pagination"""
    # Create multiple items to test pagination
    for i in range(5):
        table(dataset=dataset_fixture, name=f'pagination_table_{i}', username=dataset_fixture.owner)
        location(dataset=dataset_fixture, name=f'pagination_folder_{i}', username=dataset_fixture.owner)

    # Test first page with page size 3
    response = client.query(
        """
        query listDatasetTablesFolders(
            $datasetUri: String!,
            $filter: DatasetFilter
        ) {
            listDatasetTablesFolders(
                datasetUri: $datasetUri,
                filter: $filter
            ) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                    name
                    targetType
                    targetUri
                }
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        datasetUri=dataset_fixture.datasetUri,
        filter={'page': 1, 'pageSize': 3},
    )

    assert not response.errors
    assert response.data.listDatasetTablesFolders.page == 1
    assert len(response.data.listDatasetTablesFolders.nodes) == 3
    assert response.data.listDatasetTablesFolders.hasNext is True
    assert response.data.listDatasetTablesFolders.hasPrevious is False

    # Test second page
    response = client.query(
        """
        query listDatasetTablesFolders(
            $datasetUri: String!,
            $filter: DatasetFilter
        ) {
            listDatasetTablesFolders(
                datasetUri: $datasetUri,
                filter: $filter
            ) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                    name
                    targetType
                    targetUri
                }
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        datasetUri=dataset_fixture.datasetUri,
        filter={'page': 2, 'pageSize': 3},
    )

    assert not response.errors
    assert response.data.listDatasetTablesFolders.page == 2
    assert len(response.data.listDatasetTablesFolders.nodes) == 3
    assert response.data.listDatasetTablesFolders.hasPrevious is True


def test_list_dataset_tables_folders_unauthorized(client, dataset_fixture):
    """Test listing with unauthorized user"""
    response = client.query(
        """
        query listDatasetTablesFolders(
            $datasetUri: String!,
            $filter: DatasetFilter
        ) {
            listDatasetTablesFolders(
                datasetUri: $datasetUri,
                filter: $filter
            ) {
                count
                nodes {
                    name
                    targetType
                    targetUri
                }
            }
        }
        """,
        username='unauthorized_user',
        datasetUri=dataset_fixture.datasetUri,
        filter={},
    )

    assert response.errors
    assert 'UnauthorizedOperation' in response.errors[0].message
