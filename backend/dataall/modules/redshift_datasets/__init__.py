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
        from dataall.modules.catalog import CatalogApiModuleInterface
        from dataall.modules.feed import FeedApiModuleInterface
        from dataall.modules.vote import VoteApiModuleInterface

        return [
            DatasetBaseApiModuleInterface,
            CatalogApiModuleInterface,
            FeedApiModuleInterface,
            VoteApiModuleInterface,
        ]

    def __init__(self):
        import dataall.modules.redshift_datasets.api

        log.info('API of Redshift datasets has been imported')


class RedshiftDatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.redshift_datasets.cdk

        log.info('Redshift Dataset CDK has been imported')
