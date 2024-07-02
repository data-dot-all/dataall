import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class BaseDataAllMigration(ABC):
    @staticmethod
    @abstractmethod
    def key() -> str:
        """
        Returns string and needs to be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def name() -> str:
        """
        Returns string and needs to be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def description() -> str:
        """
        Returns string and needs to be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def next_migration():
        """
        Returns next migraton class and needs to be implemented in the  inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def up():
        """
        Performs upgrade and needs to be implemented in the inherited classes
        """
        ...

    @staticmethod
    @abstractmethod
    def down():
        """
        Performs downgrade and needs to be implemented in the inherited classes
        """
        ...
