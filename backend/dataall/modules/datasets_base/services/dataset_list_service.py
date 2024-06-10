import logging
from sqlalchemy.orm import Query
from typing import List
from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.datasets_base.services.dataset_service_interface import DatasetServiceInterface
from dataall.modules.datasets_base.db.dataset_repositories import DatasetListRepository
from dataall.modules.datasets_base.services.dataset_list_permissions import LIST_ENVIRONMENT_DATASETS

log = logging.getLogger(__name__)


class DatasetListService:
    _interfaces: List[DatasetServiceInterface] = []

    @classmethod
    def register(cls, interface: DatasetServiceInterface):
        cls._interfaces.append(interface)

    @classmethod
    def _list_all_user_interface_datasets(cls, session, username, groups) -> List[Query]:
        """All list_datasets from other modules that need to be appended to the list of datasets"""
        return [
            query
            for interface in cls._interfaces
            for query in [interface.append_to_list_user_datasets(session, username, groups)]
            if query.first() is not None
        ]

    @classmethod
    def get_other_modules_dataset_user_role(cls, session, uri, username, groups) -> str:
        """All other user role types that might come from other modules"""
        for interface in cls._interfaces:
            role = interface.resolve_additional_dataset_user_role(session, uri, username, groups)
            if role is not None:
                return role
        return None

    @staticmethod
    def list_all_user_datasets(data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            all_subqueries = DatasetListService._list_all_user_interface_datasets(
                session, context.username, context.groups
            )
            return DatasetListRepository.paginated_all_user_datasets(
                session, context.username, context.groups, all_subqueries, data=data
            )

    @staticmethod
    def list_owned_datasets(data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return DatasetListRepository.paginated_user_datasets(session, context.username, context.groups, data=data)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def list_datasets_created_in_environment(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetListRepository.paginated_environment_datasets(
                session=session,
                uri=uri,
                data=data,
            )
