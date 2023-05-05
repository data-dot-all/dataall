import logging
from typing import List, Type

from dataall.modules.datasets_base import DatasetBaseModuleInterface
from dataall.modules.loader import ModuleInterface, ImportMode


log = logging.getLogger(__name__)


class SharingApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: List[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [DatasetBaseModuleInterface]

    def __init__(self):
        from dataall.modules.dataset_sharing import api
        log.info("API of dataset sharing has been imported")
