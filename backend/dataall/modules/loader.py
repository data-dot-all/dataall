"""Load modules that are specified in the configuration file"""
import importlib
import inspect
import logging
from enum import Enum
from typing import List, Protocol, runtime_checkable

from dataall.core.config import config

log = logging.getLogger(__name__)

_MODULE_PREFIX = "dataall.modules"
_IMPORTED = []


class ImportMode(Enum):
    """Defines importing mode

    Since there are different infrastructure components that requires only part
    of functionality to be loaded, there should be different loading modes

    Keys represent loading mode while value a suffix im module loading.
    For example, API will try to load a graphql functionality under a module directory
    The values represent a submodule and should exist
    """

    API = "api"
    CDK = "cdk"
    TASKS = "tasks"


@runtime_checkable
class ModuleInterface(Protocol):
    # An interface of the module. The implementation should be part of __init__.py of the module

    def initialize(self, modes: List[ImportMode]):
        # Initialize the module
        ...


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
    for module in modules:
        name, props = module.popitem()
        active = props["active"]

        if not active:
            raise ValueError(f"Status is not defined for {name} module")

        if active.lower() != "true":
            log.info(f"Module {name} is not active. Skipping...")
            continue

        if active.lower() == "true" and not _import_module(name):
            raise ValueError(f"Couldn't find module {name} under modules directory")

        log.info(f"Module {name} is loaded")

    log.info("Initiating all modules")

    for interface in _IMPORTED:
        interface.initialize(modes)

    log.info("All modules have been imported and initiated")


def _import_module(name):
    try:
        module = importlib.import_module(f"{_MODULE_PREFIX}.{name}")
        _inspect_module_interface(module)

        return True
    except ModuleNotFoundError:
        return False


def _inspect_module_interface(module):
    classes = inspect.getmembers(module, inspect.isclass)
    for class_name, _class in classes:
        if issubclass(_class, ModuleInterface):
            _IMPORTED.append(_class())
            return

    raise ImportError(f"No class implementing ModuleInterface in {module}")
