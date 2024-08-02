import logging
from abc import ABC, abstractmethod
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes

log = logging.getLogger(__name__)


class DatasetServiceInterface(ABC):
    """
    Interface for modules that depend on datasets to insert code in datasets and avoid circular dependencies
    For example, we might check dataset_shares (in dataset_sharing module) before deleting (datasets_module)
    """

    @property
    @abstractmethod
    def dataset_type(self) -> DatasetTypes: ...

    @staticmethod
    @abstractmethod
    def check_before_delete(session, uri, **kwargs) -> bool:
        """Abstract method to be implemented by dependent modules that want to add checks before deletion for dataset objects"""
        ...

    @staticmethod
    @abstractmethod
    def execute_on_delete(session, uri, **kwargs) -> bool:
        """Abstract method to be implemented by dependent modules that want to add clean-up actions when a dataset object is deleted"""
        ...

    @staticmethod
    @abstractmethod
    def append_to_list_user_datasets(session, username, groups):
        """Abstract method to be implemented by dependent modules that want to add datasets to the list_datasets that list all datasets that the user has access to"""
        ...

    @staticmethod
    @abstractmethod
    def resolve_additional_dataset_user_role(session, uri, username, groups):
        """Abstract method to be implemented by dependent modules that want to add new types of user role in relation to a Dataset"""
        ...

    @staticmethod
    @abstractmethod
    def extend_attach_steward_permissions(session, dataset, new_stewards) -> bool:
        """Abstract method to be implemented by dependent modules that want to attach additional permissions to Dataset stewards"""
        ...

    @staticmethod
    @abstractmethod
    def extend_delete_steward_permissions(session, dataset, new_stewards) -> bool:
        """Abstract method to be implemented by dependent modules that want to attach additional permissions to Dataset stewards"""
        ...
