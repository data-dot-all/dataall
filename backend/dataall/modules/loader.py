"""Load modules that are specified in the configuration file"""
import importlib
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from dataall.core.config import config

log = logging.getLogger(__name__)

_MODULE_PREFIX = "dataall.modules"


class ImportMode(Enum):
    """Defines importing mode

    Since there are different infrastructure components that requires only part
    of functionality to be loaded, there should be different loading modes
    """

    API = "api"
    CDK = "cdk"
    TASKS = "tasks"


class ModuleInterface(ABC):
    """
    An interface of the module. The implementation should be part of __init__.py of the module
    Contains an API that will be called from core part
    """
    @classmethod
    @abstractmethod
    def is_supported(cls, modes: List[ImportMode]):
        pass


def load_modules(modes: List[ImportMode]) -> None:
    """
    Loads all modules from the config
    Loads only requested functionality (submodules) using the mode parameter
    """
    try:
        modules = config.get_property("modules")
    except KeyError:
        log.info('"modules" has not been found in the config file. Nothing to load')
        return

    log.info("Found %d modules that have been found in the config", len(modules))
    for name, props in modules.items():
        active = props["active"]

        if not active:
            raise ValueError(f"Status is not defined for {name} module")

        if active.lower() != "true":
            log.info(f"Module {name} is not active. Skipping...")
            continue

        if active.lower() == "true" and not _import_module(name):
            raise ValueError(f"Couldn't find module {name} under modules directory")

        log.info(f"Module {name} is loaded")

    for module in ModuleInterface.__subclasses__():
        if module.is_supported(modes):
            module()

    log.info("All modules have been imported")


def _import_module(name):
    try:
        importlib.import_module(f"{_MODULE_PREFIX}.{name}")
        return True
    except ModuleNotFoundError:
        return False
