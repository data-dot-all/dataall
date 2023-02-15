"""Load modules that are specified in the configuration file"""
import importlib
import logging
from dataall.core.config import config

log = logging.getLogger(__name__)

_MODULE_PREFIX = "dataall.modules"


def load_modules() -> None:
    """Loads all modules from the config"""
    try:
        modules = config.get_property("modules")
    except KeyError:
        log.info('"modules" has not been found in the config file. Nothing to load')
        return

    log.info("Loading %d modules that have been found in the config", len(modules))
    for module in modules:
        _import_module(module)


def _import_module(name: str) -> None:
    """Import a module with the given name."""
    try:
        importlib.import_module(f'{_MODULE_PREFIX}.{name}')
        log.info("Imported module %s", name)
    except ModuleNotFoundError:
        log.error("Couldn't find module %s under modules directory", name)
