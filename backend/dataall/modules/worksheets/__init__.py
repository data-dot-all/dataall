"""Contains the code related to worksheets"""
import logging
from typing import List, Type

from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.base.loader import ImportMode, ModuleInterface
from dataall.modules.feed import FeedApiModuleInterface
from dataall.modules.worksheets.db.models import Worksheet
from dataall.modules.worksheets.db.worksheets_repository import WorksheetRepository

log = logging.getLogger(__name__)


class WorksheetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for worksheet GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [FeedApiModuleInterface]

    def __init__(self):
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition

        import dataall.modules.worksheets.api

        FeedRegistry.register(FeedDefinition("Worksheet", Worksheet))

        EnvironmentResourceManager.register(WorksheetRepository())

        log.info("API of worksheets has been imported")
