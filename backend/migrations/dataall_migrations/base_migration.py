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
    def previous_migration() -> str:
        """
        Returns string and needs to be implemented in the  inherited classes
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

    @classmethod
    def set_next(cls, next_migration_key):
        if 'next_migration' in cls.__dict__ and cls.next_migration is not None:
            raise Exception(
                f'Conflict. Migrations {next_migration_key} and {cls.next_migration} have the same parent {cls.key()}'
            )
        cls.next_migration = next_migration_key

    @classmethod
    def next(cls):
        if 'next_migration' in cls.__dict__:
            return cls.next_migration
        return None

    @classmethod
    def is_initial(cls):
        return cls.previous_migration() is None

    @classmethod
    def is_last(cls):
        return 'next_migration' not in cls.__dict__ or cls.next_migration is None
