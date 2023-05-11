from dataall.aws.handlers.service_handlers import Worker
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission
from dataall.db.api import Environment
from dataall.db.models import Task
from dataall.modules.datasets import DatasetLocationIndexer
from dataall.modules.datasets.aws.s3_location_client import S3LocationClient
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository
from dataall.modules.datasets.db.dataset_service import DatasetService
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_FOLDER, MANAGE_DATASETS, \
    CREATE_DATASET_FOLDER, LIST_DATASET_FOLDERS, DELETE_DATASET_FOLDER


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
            location = DatasetLocationRepository.create_dataset_location(
                session=session,
                uri=uri,
                data=data,
            )

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
            data['location'] = location
            data['locationUri'] = location.locationUri
            DatasetLocationRepository.update_dataset_location(
                session=session,
                uri=location.datasetUri,
                data=data,
            )
            DatasetLocationIndexer.upsert(session, folder_uri=location.locationUri)

            return location

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(DELETE_DATASET_FOLDER, parent_resource=_get_dataset_uri)
    def remove_storage_location(uri: str = None):
        with get_context().db_engine.scoped_session() as session:
            location = DatasetLocationRepository.get_location_by_uri(session, uri)
            DatasetLocationRepository.delete_dataset_location(
                session=session,
                uri=location.datasetUri,
                data={'locationUri': location.locationUri},
            )
            DatasetLocationIndexer.delete_doc(doc_id=location.locationUri)
        return True

    @staticmethod
    @has_resource_permission(UPDATE_DATASET_FOLDER, parent_resource=_get_dataset_uri)
    def publish_location_update(uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            location = DatasetLocationRepository.get_location_by_uri(session, uri)
            dataset = DatasetService.get_dataset_by_uri(session, location.datasetUri)
            env = Environment.get_environment_by_uri(session, dataset.environmentUri)
            if not env.subscriptionsEnabled or not env.subscriptionsProducersTopicName:
                raise Exception(
                    'Subscriptions are disabled. '
                    "First enable subscriptions for this dataset's environment then retry."
                )
            task = Task(
                targetUri=location.datasetUri,
                action='sns.dataset.publish_update',
                payload={'s3Prefix': location.S3Prefix},
            )
            session.add(task)

        Worker.process(engine=context.db_engine, task_ids=[task.taskUri], save_response=False)
        return True
