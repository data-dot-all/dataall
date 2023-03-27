"""Load modules that are specified in the configuration file"""
import importlib
import logging
from enum import Enum
from typing import List

from dataall.core.config import config

log = logging.getLogger(__name__)

_MODULE_PREFIX = "dataall.modules"


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

    log.info("Loading %d modules that have been found in the config", len(modules))
    for module in modules:
        name, props = module.popitem()
        active = props["active"]

        if not active:
            raise ValueError(f"Status is not defined for {name} module")

        if active.lower() == "true" and not _import_module(name):
            raise ValueError(f"Couldn't find module {name} under modules directory")


def _import_module(module):
    try:
        importlib.import_module(f'{_MODULE_PREFIX}.{module}')
        return True
    except ModuleNotFoundError:
        return False


def _import_submodule(module: str, mode: ImportMode) -> None:
    """Import a module with the given name."""
    full_name = f"{_MODULE_PREFIX}.{module}.{mode.value}"
    try:
        importlib.import_module(full_name)
        log.info("Imported module %s", full_name)
    except ModuleNotFoundError:
        raise ValueError(f"{mode.value} submodule can't be found under {full_name}")
