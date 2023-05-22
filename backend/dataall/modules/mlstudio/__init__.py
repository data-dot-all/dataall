"""Contains the code related to SageMaker ML Studio user profiles"""
import logging

from dataall.db.api import TargetType
from dataall.modules.loader import ImportMode, ModuleInterface
from dataall.modules.mlstudio.db.mlstudio_repository import SageMakerStudioRepository

log = logging.getLogger(__name__)


class MLStudioApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.mlstudio.api
        from dataall.modules.mlstudio.services.mlstudio_permissions import GET_SGMSTUDIO_USER, UPDATE_SGMSTUDIO_USER
        TargetType("mlstudio", GET_SGMSTUDIO_USER, UPDATE_SGMSTUDIO_USER)

        log.info("API of sagemaker mlstudio has been imported")


class MLStudioCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio ecs tasks"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.mlstudio.cdk
        log.info("API of sagemaker mlstudio has been imported")
