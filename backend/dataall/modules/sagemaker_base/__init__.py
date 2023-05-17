"""Common code for machine learning studio and notebooks"""
from typing import Set

from dataall.modules.loader import ModuleInterface, ImportMode


class SagemakerCdkModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CDK in modes
