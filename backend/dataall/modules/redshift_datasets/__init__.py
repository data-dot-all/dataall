"""Contains the code related to datasets"""

import logging
from typing import List, Type, Set

from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class RedshiftDatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseApiModuleInterface
        from dataall.modules.connections_base import ConnectionsBaseModuleInterface
        from dataall.modules.catalog import CatalogApiModuleInterface
        from dataall.modules.feed import FeedApiModuleInterface
        from dataall.modules.vote import VoteApiModuleInterface

        return [
            DatasetBaseApiModuleInterface,
            CatalogApiModuleInterface,
            ConnectionsBaseModuleInterface,
            FeedApiModuleInterface,
            VoteApiModuleInterface,
        ]

    def __init__(self):
        import dataall.modules.redshift_datasets.api

        log.info('API of Redshift datasets has been imported')


class RedshiftDatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.HANDLERS in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.connections_base import ConnectionsBaseModuleInterface

        return [DatasetBaseModuleInterface, ConnectionsBaseModuleInterface]

    def __init__(self):
        import dataall.modules.redshift_datasets.handlers

        log.info('Redshift Dataset handlers have been imported')


class RedshiftDatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.CDK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.connections_base import ConnectionsBaseModuleInterface

        return [DatasetBaseModuleInterface, ConnectionsBaseModuleInterface]

    def __init__(self):
        import dataall.modules.redshift_datasets.cdk

        log.info('Redshift Dataset CDK has been imported')
