from typing import Set

from dataall.base.loader import ModuleInterface, ImportMode


class FeedApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for feeds code in GraphQL Lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.feed.api
