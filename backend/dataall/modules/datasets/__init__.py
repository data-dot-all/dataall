"""Contains the code related to datasets"""
import logging
from dataall.modules.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notebook GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.datasets.api
        log.info("API of datasets has been imported")

