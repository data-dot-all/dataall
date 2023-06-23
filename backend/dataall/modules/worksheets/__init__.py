"""Contains the code related to worksheets"""
import logging

from dataall.core.group.services.environment_resource_manager import EnvironmentResourceManager
from dataall.modules.loader import ImportMode, ModuleInterface
from dataall.modules.worksheets.db.models import Worksheet
from dataall.modules.worksheets.db.repositories import WorksheetRepository

log = logging.getLogger(__name__)


class WorksheetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for worksheet GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    def __init__(self):
        from dataall.api.Objects.Feed.registry import FeedRegistry, FeedDefinition

        import dataall.modules.worksheets.api

        FeedRegistry.register(FeedDefinition("Worksheet", Worksheet))

        EnvironmentResourceManager.register(WorksheetRepository())

        log.info("API of worksheets has been imported")
