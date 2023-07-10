from dataall.base.context import get_context
from dataall.core.glossary.db.glossary import Glossary
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.db.exceptions import ResourceShared, ResourceAlreadyExists
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository
from dataall.modules.datasets.aws.s3_location_client import S3LocationClient
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository
from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_FOLDER, MANAGE_DATASETS, \
    CREATE_DATASET_FOLDER, LIST_DATASET_FOLDERS, DELETE_DATASET_FOLDER
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository


class DatasetLocationService:
    @staticmethod
    def _get_dataset_uri(session, uri):
        location = DatasetLocationRepository.get_location_by_uri(session, uri)
        return location.datasetUri

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(CREATE_DATASET_FOLDER)
    def create_storage_location(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            exists = DatasetLocationRepository.exists(session, uri, data['prefix'])

            if exists:
                raise ResourceAlreadyExists(
                    action='Create Folder',
                    message=f'Folder: {data["prefix"]} already exist on dataset {uri}',
                )

            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            location = DatasetLocationRepository.create_dataset_location(session, dataset, data)

            if 'terms' in data.keys():
                DatasetLocationService._create_glossary_links(session, location, data['terms'])

            S3LocationClient(location).create_bucket_prefix()

        DatasetLocationIndexer.upsert(session=session, folder_uri=location.locationUri)
        return location

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(LIST_DATASET_FOLDERS)
    def list_dataset_locations(uri: str, filter: dict = None):
        with get_context().db_engine.scoped_session() as session:
            return DatasetLocationRepository.list_dataset_locations(
                session=session, uri=uri, data=filter
            )

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(LIST_DATASET_FOLDERS, parent_resource=_get_dataset_uri)
    def get_storage_location(uri):
        with get_context().db_engine.scoped_session() as session:
            return DatasetLocationRepository.get_location_by_uri(session, uri)

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET_FOLDER, parent_resource=_get_dataset_uri)
    def update_storage_location(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            location = DatasetLocationRepository.get_location_by_uri(session, uri)
            for k in data.keys():
                setattr(location, k, data.get(k))

            if 'terms' in data.keys():
                DatasetLocationService._create_glossary_links(session, location, data['terms'])

            DatasetLocationIndexer.upsert(session, folder_uri=location.locationUri)

            return location

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(DELETE_DATASET_FOLDER, parent_resource=_get_dataset_uri)
    def remove_storage_location(uri: str = None):
        with get_context().db_engine.scoped_session() as session:
            location = DatasetLocationRepository.get_location_by_uri(session, uri)
            has_shares = ShareObjectRepository.has_shared_items(session, location.locationUri)
            if has_shares:
                raise ResourceShared(
                    action=DELETE_DATASET_FOLDER,
                    message='Revoke all folder shares before deletion',
                )

            ShareObjectRepository.delete_shares(session, location.locationUri)
            DatasetLocationRepository.delete(session, location)
            Glossary.delete_glossary_terms_links(
                session,
                target_uri=location.locationUri,
                target_type='DatasetStorageLocation',
            )
            DatasetLocationIndexer.delete_doc(doc_id=location.locationUri)
        return True

    @staticmethod
    def _create_glossary_links(session, location, terms):
        Glossary.set_glossary_terms_links(
            session,
            get_context().username,
            location.locationUri,
            'DatasetStorageLocation',
            terms
        )
