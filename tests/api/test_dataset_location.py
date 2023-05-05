import typing

import pytest

import dataall
from dataall.modules.datasets_base.db.models import Dataset


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant):
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset1(env1, org1, dataset, group) -> Dataset:
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


def test_get_dataset(client, dataset1, env1, user, group):
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
        groups=[group.name],
    )
    assert response.data.getDataset.AwsAccountId == env1.AwsAccountId
    assert response.data.getDataset.region == env1.region
    assert response.data.getDataset.label == 'dataset1'
    assert response.data.getDataset.imported is False
    assert response.data.getDataset.importedS3Bucket is False


def test_create_location(client, dataset1, env1, user, group, patch_es, module_mocker):
    module_mocker.patch(
        'dataall.modules.datasets.handlers.s3_location_handler.S3DatasetLocationHandler.create_bucket_prefix',
        return_value=True
    )
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
        username=user.userName,
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


def test_manage_dataset_location(client, dataset1, env1, user, group):
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
                locations{
                    nodes{
                        locationUri
                    }
                }
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username=user.userName,
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
        username=user.userName,
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
        username=user.userName,
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
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteDatasetStorageLocation
