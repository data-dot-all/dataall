"""Contains the code related to SageMaker ML Studio user profiles"""
import logging

from dataall.base.loader import ImportMode, ModuleInterface
from dataall.core.stacks.db.target_type_repositories import TargetType
from dataall.modules.mlstudio.db.mlstudio_repositories import SageMakerStudioRepository
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager

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

        EnvironmentResourceManager.register(SageMakerStudioRepository())

        log.info("API of sagemaker mlstudio has been imported")


class MLStudioCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio ecs tasks"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.mlstudio.cdk
        from dataall.core.environment.cdk.environment_stack import EnvironmentSetup
        from dataall.modules.mlstudio.cdk.mlstudio_extension import SageMakerDomainExtension

        EnvironmentSetup.register(SageMakerDomainExtension)
        log.info("API of sagemaker mlstudio has been imported")
