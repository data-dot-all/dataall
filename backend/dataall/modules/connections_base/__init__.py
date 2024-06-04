from typing import Set
from dataall.base.loader import ModuleInterface, ImportMode


class ConnectionsBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {ImportMode.CDK, ImportMode.HANDLERS, ImportMode.API}
        return modes & supported_modes

    def __init__(self):
        import dataall.modules.connections_base.api
        import dataall.modules.connections_base.api.enums
