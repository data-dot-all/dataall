import logging
from typing import List

from dataall.modules.loader import ModuleInterface, ImportMode


log = logging.getLogger(__name__)


class SharingApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: List[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        log.info("API pf dataset sharing has been imported")
