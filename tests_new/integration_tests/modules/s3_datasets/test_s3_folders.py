import logging
import pytest
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import create_folder, delete_folder, update_folder, get_folder
from integration_tests.errors import GqlError

from integration_tests.modules.s3_datasets.conftest import (
    FOLDERS_FIXTURES_PARAMS,
    DATASETS_FIXTURES_PARAMS,
)

log = logging.getLogger(__name__)


@pytest.mark.parametrize(*FOLDERS_FIXTURES_PARAMS)
def test_create_folder(client1, folders_fixture_name, request):
    folders = request.getfixturevalue(folders_fixture_name)
    folder = folders[0]
    assert_that(folder.S3Prefix).is_equal_to('sessionFolderA')
    assert_that(folder.label).is_equal_to('labelSessionFolderA')


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1'],
)
def test_create_folder_unauthorized(client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    assert_that(create_folder).raises(GqlError).when_called_with(
        client2, dataset_uri, {'prefix': 'badFolder', 'label': 'badFolder'}
    ).contains('UnauthorizedOperation', 'CREATE_DATASET_FOLDER', dataset_uri)


@pytest.mark.parametrize(*FOLDERS_FIXTURES_PARAMS)
def test_get_folder(client1, folders_fixture_name, request):
    folders = request.getfixturevalue(folders_fixture_name)
    folder = folders[0]
    response = get_folder(client1, locationUri=folder.locationUri)
    assert_that(response.S3Prefix).is_equal_to('sessionFolderA')
    assert_that(response.label).is_equal_to('labelSessionFolderA')


@pytest.mark.parametrize(*FOLDERS_FIXTURES_PARAMS)
def test_update_folder(client1, folders_fixture_name, request):
    folders = request.getfixturevalue(folders_fixture_name)
    folder = folders[0]
    response = update_folder(client1, locationUri=folder.locationUri, input={'label': 'newLabel'})
    assert_that(response.label).is_equal_to('newLabel')


@pytest.mark.parametrize(
    'dataset_fixture_name,folders_fixture_name',
    [('session_s3_dataset1', 'session_s3_dataset1_folders')],
)
def test_update_folder_unauthorized(client2, dataset_fixture_name, folders_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    folder = request.getfixturevalue(folders_fixture_name)[0]
    assert_that(update_folder).raises(GqlError).when_called_with(
        client2, locationUri=folder.locationUri, input={'label': 'newLabel'}
    ).contains('UnauthorizedOperation', 'UPDATE_DATASET_FOLDER', dataset.datasetUri)


@pytest.mark.parametrize(*DATASETS_FIXTURES_PARAMS)
def test_delete_folder(client1, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    location = create_folder(
        client1, datasetUri=dataset_uri, input={'prefix': 'folderToDelete', 'label': 'folderToDelete'}
    )
    response = delete_folder(client1, location.locationUri)
    assert_that(response).is_equal_to(True)


@pytest.mark.parametrize(
    'dataset_fixture_name',
    ['session_s3_dataset1'],
)
def test_delete_folder_unauthorized(client1, client2, dataset_fixture_name, request):
    dataset = request.getfixturevalue(dataset_fixture_name)
    dataset_uri = dataset.datasetUri
    location = create_folder(
        client1, datasetUri=dataset_uri, input={'prefix': 'badFolderToDelete', 'label': 'badFolderToDelete'}
    )
    assert_that(delete_folder).raises(GqlError).when_called_with(client2, location.locationUri).contains(
        'UnauthorizedOperation', 'DELETE_DATASET_FOLDER', dataset_uri
    )
