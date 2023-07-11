"""Contains the code related to SageMaker notebooks"""
import logging

from dataall.base.loader import ImportMode, ModuleInterface
from dataall.core.stacks.db.target_type import TargetType

log = logging.getLogger(__name__)


class NotebookApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notebook GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.notebooks.api

        from dataall.modules.notebooks.services.notebook_permissions import GET_NOTEBOOK, UPDATE_NOTEBOOK
        TargetType("notebook", GET_NOTEBOOK, UPDATE_NOTEBOOK)

        log.info("API of sagemaker notebooks has been imported")


class NotebookCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notebook ecs tasks"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.notebooks.cdk
        log.info("API of sagemaker notebooks has been imported")
