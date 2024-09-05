import logging
from assertpy import assert_that

from integration_tests.modules.s3_datasets.queries import create_folder, delete_folder, update_folder, get_folder
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_create_folder(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    folder = folders[0]
    assert_that(folder.S3Prefix).is_equal_to('sessionFolderA')
    assert_that(folder.label).is_equal_to('labelSessionFolderA')


def test_create_folder_unauthorized(client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    assert_that(create_folder).raises(GqlError).when_called_with(
        client2, dataset_uri, {'prefix': 'badFolder', 'label': 'badFolder'}
    ).contains('UnauthorizedOperation', 'CREATE_DATASET_FOLDER', dataset_uri)


def test_update_folder(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    folder = folders[0]
    response = update_folder(client1, locationUri=folder.locationUri, input={'label': 'newLabel'})
    assert_that(response.label).is_equal_to('newLabel')


def test_update_folder_unauthorized(client2, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    folder = folders[0]
    assert_that(update_folder).raises(GqlError).when_called_with(
        client2, locationUri=folder.locationUri, input={'label': 'newLabel'}
    ).contains('UnauthorizedOperation', 'UPDATE_DATASET_FOLDER', dataset.datasetUri)


def test_delete_folder(client1, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    location = create_folder(
        client1, datasetUri=dataset_uri, input={'prefix': 'folderToDelete', 'label': 'folderToDelete'}
    )
    response = delete_folder(client1, location.locationUri)
    assert_that(response).is_equal_to(True)


def test_delete_folder_unauthorized(client1, client2, session_s3_dataset1):
    dataset_uri = session_s3_dataset1.datasetUri
    location = create_folder(
        client1, datasetUri=dataset_uri, input={'prefix': 'badFolderToDelete', 'label': 'badFolderToDelete'}
    )
    assert_that(delete_folder).raises(GqlError).when_called_with(client2, location.locationUri).contains(
        'UnauthorizedOperation', 'DELETE_DATASET_FOLDER', dataset_uri
    )


def test_get_folder(client1, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    folder = folders[0]
    response = get_folder(client1, locationUri=folder.locationUri)
    assert_that(response.S3Prefix).is_equal_to('sessionFolderA')
    assert_that(response.label).is_equal_to('labelSessionFolderA')


def test_get_folder_unauthorized(client2, session_s3_dataset2_with_tables_and_folders):
    dataset, tables, folders = session_s3_dataset2_with_tables_and_folders
    folder = folders[0]
    assert_that(get_folder).raises(GqlError).when_called_with(client2, locationUri=folder.locationUri).contains(
        'UnauthorizedOperation', 'GET_DATASET_FOLDER', folder.locationUri
    )
