"""Contains the code related to dashboards"""
import logging

from dataall.modules.loader import ImportMode, ModuleInterface

log = logging.getLogger(__name__)


class DashboardApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dashboard GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.dashboards.api
