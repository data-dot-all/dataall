import logging
import os
from abc import ABC, abstractmethod
from typing import Type, Union

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class MigrationBase(ABC):
    @classmethod
    @abstractmethod
    def revision_id(cls) -> str:
        """
        Uniq revision identifier.
        """
        ...

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        """
        Short description of migration logic and purpose.
        """
        ...

    @classmethod
    @abstractmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        """
        Returns next migration class
        """
        ...

    @classmethod
    @abstractmethod
    def up(cls) -> None:
        """
        Performs upgrade
        """
        ...

    @classmethod
    @abstractmethod
    def down(cls) -> None:
        """
        Performs downgrade
        """
        ...
