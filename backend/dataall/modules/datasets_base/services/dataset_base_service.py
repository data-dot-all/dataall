import logging
from abc import ABC, abstractmethod

from dataall.base.context import get_context
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.datasets_base.services.dataset_base_permissions import (
    DELETE_DATASET,
    MANAGE_DATASETS,
    UPDATE_DATASET,
    LIST_ENVIRONMENT_DATASETS,
    CREATE_DATASET
)
from dataall.modules.datasets_base.db.dataset_base_repositories import DatasetBaseRepository


log = logging.getLogger(__name__)


class DatasetListService:

    #TODO: define this method in data_sharing_base to avoid circular dependency
    # @staticmethod
    # def list_owned_shared_datasets(data: dict):
    #     context = get_context()
    #     with context.db_engine.scoped_session() as session:
    #         return ShareObjectRepository.paginated_user_datasets(session, context.username, context.groups, data=data)

    @staticmethod
    def list_owned_datasets(data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return DatasetBaseRepository.paginated_user_datasets(session, context.username, context.groups, data=data)

    #TODO: define in data_sharing_base module to avoid circular dependency
    # @staticmethod
    # def list_dataset_share_objects(dataset: Dataset, data: dict = None):
    #     with get_context().db_engine.scoped_session() as session:
    #         return ShareObjectRepository.paginated_dataset_shares(session=session, uri=dataset.datasetUri, data=data)
    #

    # @staticmethod
    # def get_dataset_stack(dataset: Dataset):
    #     return stack_helper.get_stack_with_cfn_resources(
    #         targetUri=dataset.datasetUri,
    #         environmentUri=dataset.environmentUri,
    #     )

    @staticmethod
    @has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def list_datasets_created_in_environment(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetBaseRepository.paginated_environment_datasets(
                session=session,
                uri=uri,
                data=data,
            )

    @staticmethod
    def list_datasets_owned_by_env_group(env_uri: str, group_uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetBaseRepository.paginated_environment_group_datasets(
                session=session,
                env_uri=env_uri,
                group_uri=group_uri,
                data=data,
            )


## TODO: feedback; maybe datasets_base and dataset_list. Can the base exist on its own. Experiment different levels inside the module
# datasets_base as core
class DatasetBaseService(ABC):

    @abstractmethod
    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS) #TODO test
    @has_resource_permission(CREATE_DATASET)
    @has_group_permission(CREATE_DATASET)
    def create_dataset(uri, admin_group, data: dict):
        pass

    @abstractmethod
    @staticmethod
    def import_dataset(uri, admin_group, data: dict):
        pass

    @abstractmethod
    @staticmethod
    @has_resource_permission(DELETE_DATASET)
    def delete_dataset(uri: str, delete_from_aws: bool = False):
        pass

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET)
    def update_dataset(uri: str, data: dict):
        pass

    @abstractmethod
    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    def get_dataset(uri):
        pass

    @staticmethod
    def delete_dataset_term_links(session, dataset_uri):
        GlossaryRepository.delete_glossary_terms_links(session, dataset_uri, 'Dataset')
