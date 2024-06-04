from typing import Set

from dataall.base.loader import ModuleInterface, ImportMode


class NotificationsModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notifications code in GraphQL or handlers"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {ImportMode.API, ImportMode.HANDLERS, ImportMode.SHARES_TASK}
        return modes & supported_modes

    def __init__(self):
        import dataall.modules.notifications.api
        import dataall.modules.notifications.handlers
