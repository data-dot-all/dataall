import pytest
from unittest.mock import MagicMock, patch

from dataall.modules.s3_datasets.services.dataset_enums import MetadataGenerationTargets


@pytest.fixture(scope='function')
def mock_bedrock_client(mocker):
    mock_client = MagicMock()
    mocker.patch('dataall.modules.s3_datasets.services.dataset_service.BedrockClient', return_value=mock_client)
    mocker.patch('dataall.modules.s3_datasets.services.dataset_table_service.BedrockClient', return_value=mock_client)
    mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_location_service.BedrockClient', return_value=mock_client
    )
    mock_client.invoke_model_dataset_metadata.return_value = {
        'description': 'Test dataset description',
        'label': 'Test Dataset Label',
        'tags': ['tag1', 'tag2'],
        'topics': ['Finances', 'Products'],
    }
    mock_client.invoke_model_table_metadata.return_value = {
        'description': 'Test table description',
        'tags': ['table_tag1', 'table_tag2'],
    }
    mock_client.invoke_model_folder_metadata.return_value = {
        'description': 'Test folder description',
        'label': 'Test Folder Label',
        'tags': ['folder_tag1', 'folder_tag2'],
    }
    return mock_client


@pytest.fixture(scope='function')
def mock_s3_client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_location_service.S3DatasetClient', return_value=mock_client
    )
    mock_client.list_bucket_files.return_value = [{'Key': 'file1.csv'}, {'Key': 'file2.json'}]
    return mock_client


def test_generate_metadata_for_dataset(client, dataset_fixture, mock_bedrock_client, group):
    """Test generating metadata for a dataset"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                label
                description
                tags
                topics
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        resourceUri=dataset_fixture.datasetUri,
        targetType=MetadataGenerationTargets.S3_Dataset.value,
        metadataTypes=['description', 'label', 'tags', 'topics'],
    )

    assert not response.errors
    assert response.data.generateMetadata[0].targetUri == dataset_fixture.datasetUri
    assert response.data.generateMetadata[0].targetType == 'S3_Dataset'
    assert response.data.generateMetadata[0].label == 'Test Dataset Label'
    assert response.data.generateMetadata[0].description == 'Test dataset description'
    assert 'tag1' in response.data.generateMetadata[0].tags
    assert 'tag2' in response.data.generateMetadata[0].tags
    assert 'Finances' in response.data.generateMetadata[0].topics
    assert 'Products' in response.data.generateMetadata[0].topics

    # Verify BedrockClient was called with correct parameters
    mock_bedrock_client.invoke_model_dataset_metadata.assert_called_once()
    args, kwargs = mock_bedrock_client.invoke_model_dataset_metadata.call_args
    assert kwargs['metadata_types'] == ['description', 'label', 'tags', 'topics']
    assert kwargs['dataset'] is not None


def test_generate_metadata_for_table(client, table_fixture, mock_bedrock_client, group):
    """Test generating metadata for a table"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                description
                tags
            }
        }
        """,
        username=table_fixture.owner,
        groups=[group.name],
        resourceUri=table_fixture.tableUri,
        targetType=MetadataGenerationTargets.Table.value,
        metadataTypes=['description', 'tags'],
    )

    assert not response.errors
    assert response.data.generateMetadata[0].targetUri == table_fixture.tableUri
    assert response.data.generateMetadata[0].targetType == 'Table'
    assert response.data.generateMetadata[0].description == 'Test table description'
    assert 'table_tag1' in response.data.generateMetadata[0].tags
    assert 'table_tag2' in response.data.generateMetadata[0].tags

    # Verify BedrockClient was called with correct parameters
    mock_bedrock_client.invoke_model_table_metadata.assert_called_once()
    args, kwargs = mock_bedrock_client.invoke_model_table_metadata.call_args
    assert kwargs['metadata_types'] == ['description', 'tags']
    assert kwargs['table'] is not None


def test_generate_metadata_for_table_with_sample_data(client, table_fixture, mock_bedrock_client, group):
    """Test generating metadata for a table with sample data"""
    sample_data = {'fields': ['{"name": "id"}', '{"name": "name"}'], 'rows': ['["1", "John"]', '["2", "Jane"]']}

    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!,
            $tableSampleData: TableSampleData
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes,
                tableSampleData: $tableSampleData
            ) {
                targetUri
                targetType
                description
                tags
            }
        }
        """,
        username=table_fixture.owner,
        groups=[group.name],
        resourceUri=table_fixture.tableUri,
        targetType=MetadataGenerationTargets.Table.value,
        metadataTypes=['description', 'tags'],
        tableSampleData=sample_data,
    )

    assert not response.errors
    assert response.data.generateMetadata[0].targetUri == table_fixture.tableUri
    assert response.data.generateMetadata[0].targetType == 'Table'

    # Verify BedrockClient was called with correct parameters
    mock_bedrock_client.invoke_model_table_metadata.assert_called()
    args, kwargs = mock_bedrock_client.invoke_model_table_metadata.call_args
    assert kwargs['metadata_types'] == ['description', 'tags']
    assert kwargs['table'] is not None
    assert kwargs['sample_data'] == sample_data


def test_generate_metadata_for_folder(
    client, folder_fixture, mock_bedrock_client, mock_s3_client, group, dataset_fixture
):
    """Test generating metadata for a folder"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                label
                description
                tags
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        resourceUri=folder_fixture.locationUri,
        targetType=MetadataGenerationTargets.Folder.value,
        metadataTypes=['description', 'label', 'tags'],
    )

    assert not response.errors
    assert response.data.generateMetadata[0].targetUri == folder_fixture.locationUri
    assert response.data.generateMetadata[0].targetType == 'Folder'
    assert response.data.generateMetadata[0].label == 'Test Folder Label'
    assert response.data.generateMetadata[0].description == 'Test folder description'
    assert 'folder_tag1' in response.data.generateMetadata[0].tags
    assert 'folder_tag2' in response.data.generateMetadata[0].tags

    # Verify BedrockClient was called with correct parameters
    mock_bedrock_client.invoke_model_folder_metadata.assert_called_once()
    args, kwargs = mock_bedrock_client.invoke_model_folder_metadata.call_args
    assert kwargs['metadata_types'] == ['description', 'label', 'tags']
    assert kwargs['folder'] is not None

    # Verify S3DatasetClient was called to list files
    mock_s3_client.list_bucket_files.assert_called_once()


def test_generate_metadata_invalid_target_type(client, dataset_fixture, mock_bedrock_client, group):
    """Test generating metadata with invalid target type"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                label
                description
                tags
                topics
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        resourceUri=dataset_fixture.datasetUri,
        targetType='InvalidType',
        metadataTypes=['description', 'label', 'tags', 'topics'],
    )

    assert response.errors
    assert 'InvalidType' in response.errors[0].message


def test_generate_metadata_invalid_metadata_type(client, dataset_fixture, mock_bedrock_client, group):
    """Test generating metadata with invalid metadata type"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                label
                description
                tags
                topics
            }
        }
        """,
        username=dataset_fixture.owner,
        groups=[dataset_fixture.SamlAdminGroupName],
        resourceUri=dataset_fixture.datasetUri,
        targetType=MetadataGenerationTargets.S3_Dataset.value,
        metadataTypes=['description', 'invalid_type'],
    )

    assert response.errors
    assert 'metadataType' in response.errors[0].message


def test_generate_metadata_unauthorized(client, dataset_fixture, mock_bedrock_client):
    """Test generating metadata with unauthorized user"""
    response = client.query(
        """
        mutation generateMetadata(
            $resourceUri: String!,
            $targetType: MetadataGenerationTargets!,
            $metadataTypes: [String]!
        ) {
            generateMetadata(
                resourceUri: $resourceUri,
                targetType: $targetType,
                metadataTypes: $metadataTypes
            ) {
                targetUri
                targetType
                label
                description
                tags
                topics
            }
        }
        """,
        username='unauthorized_user',
        resourceUri=dataset_fixture.datasetUri,
        targetType=MetadataGenerationTargets.S3_Dataset.value,
        metadataTypes=['description', 'label', 'tags', 'topics'],
    )

    assert response.errors
    assert 'UnauthorizedOperation' in response.errors[0].message
