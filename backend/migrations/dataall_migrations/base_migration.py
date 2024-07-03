import logging
import os
from abc import ABC, abstractmethod
from typing import Type

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class MigrationBase(ABC):
    @staticmethod
    @abstractmethod
    def revision_id() -> str:
        """
        Uniq revision identifier.  To be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def description() -> str:
        """
        Short description of migration logic and purpose. To be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def next_migration() -> Type['MigrationBase'] | None:
        """
        Returns next migration class and needs to be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def up() -> None:
        """
        Performs upgrade and needs to be implemented in the inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def down() -> None:
        """
        Performs downgrade and needs to be implemented in the inherited classes
        """
        ...
