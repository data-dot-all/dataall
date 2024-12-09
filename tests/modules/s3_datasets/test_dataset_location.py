from unittest.mock import MagicMock
import pytest

from dataall.base.config import config
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset


@pytest.fixture(scope='module')
def dataset1(env_fixture, org_fixture, dataset, group) -> S3Dataset:
    yield dataset(org=org_fixture, env=env_fixture, name='dataset1', owner=env_fixture.owner, group=group.name)


@pytest.mark.skipif(
    not config.get_property('modules.s3_datasets.features.file_actions'), reason='Feature Disabled by Config'
)
def test_create_location(client, dataset1, user, group, patch_es, module_mocker):
    mock_client = MagicMock()
    module_mocker.patch('dataall.modules.s3_datasets.services.dataset_location_service.S3LocationClient', mock_client)
    response = client.query(
        """
        mutation createDatasetStorageLocation($datasetUri:String!, $input:NewDatasetStorageLocationInput!){
            createDatasetStorageLocation(datasetUri:$datasetUri, input:$input){
                locationUri
                S3Prefix
                label
                tags
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username=user.username,
        groups=[group.name],
        input={
            'label': 'testing',
            'prefix': 'mylocation',
            'tags': ['test'],
            'terms': ['term'],
        },
    )
    assert response.data.createDatasetStorageLocation.label == 'testing'
    assert response.data.createDatasetStorageLocation.S3Prefix == 'mylocation'
    assert 'test' in response.data.createDatasetStorageLocation.tags


@pytest.mark.skipif(
    not config.get_property('modules.s3_datasets.features.file_actions'), reason='Feature Disabled by Config'
)
def test_manage_dataset_location(client, dataset1, user, group):
    response = client.query(
        """
        query GetDataset($datasetUri:String!){
            getDataset(datasetUri:$datasetUri){
                label
                description
                restricted {
                  AwsAccountId
                  region
                }
                locations{
                    nodes{
                        locationUri
                    }
                }
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDataset.locations.nodes[0].locationUri

    response = client.query(
        """
        query getDatasetStorageLocation($locationUri:String!){
            getDatasetStorageLocation(locationUri:$locationUri){
                locationUri
                S3Prefix
                label
                tags
            }
        }
        """,
        locationUri=response.data.getDataset.locations.nodes[0].locationUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDatasetStorageLocation.label == 'testing'
    assert response.data.getDatasetStorageLocation.S3Prefix == 'mylocation'

    response = client.query(
        """
        mutation updateDatasetStorageLocation($locationUri:String!, $input:ModifyDatasetStorageLocationInput!){
            updateDatasetStorageLocation(locationUri:$locationUri, input:$input){
               locationUri
                S3Prefix
                label
                tags
            }
        }
        """,
        locationUri=response.data.getDatasetStorageLocation.locationUri,
        username=user.username,
        input={'label': 'testing2', 'terms': ['ert']},
        groups=[group.name],
    )
    assert response.data.updateDatasetStorageLocation.label == 'testing2'
    assert response.data.updateDatasetStorageLocation.S3Prefix == 'mylocation'
    assert 'test' in response.data.updateDatasetStorageLocation.tags

    response = client.query(
        """
        mutation deleteDatasetStorageLocation($locationUri: String!){
            deleteDatasetStorageLocation(locationUri:$locationUri)
        }
        """,
        locationUri=response.data.updateDatasetStorageLocation.locationUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.deleteDatasetStorageLocation
