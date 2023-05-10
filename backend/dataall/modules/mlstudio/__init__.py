"""Contains the code related to SageMaker ML Studio user profiles"""
import logging

from dataall.db.api import TargetType
from dataall.modules.loader import ImportMode, ModuleInterface
from dataall.modules.mlstudio.db.repositories import MLStudioRepository

log = logging.getLogger(__name__)


class MLStudioApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.mlstudio.api
        log.info("API of sagemaker mlstudio has been imported")
        # TODO: ask around permissions in notebooks


class MLStudioCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio ecs tasks"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.mlstudio.cdk
        log.info("API of sagemaker mlstudio has been imported")
