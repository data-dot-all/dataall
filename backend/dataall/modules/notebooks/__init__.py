"""Contains the code related to SageMaker notebooks"""
import logging

from dataall.db.api import TargetType
from dataall.modules.loader import ImportMode, ModuleInterface
from dataall.modules.notebooks.db.repositories import NotebookRepository

log = logging.getLogger(__name__)


class NotebookApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notebook GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.notebooks.api

        from dataall.modules.notebooks.services.permissions import GET_NOTEBOOK, UPDATE_NOTEBOOK
        TargetType("notebook", GET_NOTEBOOK, UPDATE_NOTEBOOK)

        log.info("API of sagemaker notebooks has been imported")


class NotebookCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for notebook ecs tasks"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.notebooks.cdk
        log.info("API of sagemaker notebooks has been imported")
