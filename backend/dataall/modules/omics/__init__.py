"""Contains the code related to HealthOmics"""

import logging
from typing import Set, List, Type

from dataall.base.loader import ImportMode, ModuleInterface
from dataall.modules.omics.db.omics_repository import OmicsRepository

log = logging.getLogger(__name__)


class OmicsApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for omics GraphQl lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.s3_datasets import DatasetApiModuleInterface

        return [DatasetApiModuleInterface]

    def __init__(self):
        import dataall.modules.omics.api

        log.info('API of omics has been imported')


class OmicsCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for omics ecs tasks"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.omics.cdk

        log.info('API of Omics has been imported')
