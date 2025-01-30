"""Load modules that are specified in the configuration file"""

import importlib
import logging
import sys
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from enum import Enum, auto
from typing import List, Type, Set

from dataall.base.config import config

log = logging.getLogger(__name__)

_MODULE_PREFIX = 'dataall.modules'

# This needed not to load the same module twice. Should happen only in tests
_ACTIVE_MODES = set()
# Contains all loaded moduels
_LOADED_MODULES: Set[str] = set()


class ImportMode(Enum):
    """Defines importing mode

    Since there are different infrastructure components that requires only part
    of functionality to be loaded, there should be different loading modes
    """

    API = auto()
    CDK = auto()
    CDK_CLI_EXTENSION = auto()
    HANDLERS = auto()
    STACK_UPDATER_TASK = auto()
    CATALOG_INDEXER_TASK = auto()
    SHARES_TASK = auto()

    @staticmethod
    def all():
        return {mode for mode in ImportMode}


class ModuleInterface(ABC):
    """
    An interface of the module. The implementation should be part of __init__.py of the module
    Contains an API that will be called from core part
    """

    @staticmethod
    @abstractmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        """
        Return True if the module interface supports any of the ImportMode and should be loaded
        """
        raise NotImplementedError('is_supported is not implemented')

    @classmethod
    def name(cls) -> str:
        """
        Returns name of the module. Should be the same if it's specified in the config file
        """
        return _remove_module_prefix(cls.__module__)

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        """
        It describes on what modules this ModuleInterface depends on.
        It will be used to eventually load these module dependencies. Even if a dependency module is not active
        in the config file.

        The default value is no dependencies
        """
        return []


def load_modules(modes: Set[ImportMode]) -> None:
    """
    Loads all modules from the config
    Loads only requested functionality (submodules) using the mode parameter
    """

    to_load = _new_modules(modes)
    if not to_load:
        return

    in_config, inactive = _load_modules()
    _check_loading_correct(in_config, to_load)
    _initialize_modules(to_load)
    _describe_loading(in_config, inactive)

    log.info('All modules have been imported')


def list_loaded_modules() -> List[str]:
    return list(_LOADED_MODULES)


def _new_modules(modes: Set[ImportMode]):
    """
    Extracts only new modules to load. It's needed to avoid multiply loading
    """
    all_modes = _ACTIVE_MODES

    to_load = modes - all_modes  # complement of set
    all_modes |= modes
    return to_load


def _load_modules():
    """
    Loads modules but not initializing them
    """
    modules = _get_modules_from_config()
    inactive = set()
    in_config = set()
    for name, props in modules.items():
        if 'active' not in props:
            raise ValueError(f'Status is not defined for {name} module')

        active = props['active']

        if not active:
            log.info(f'Module {name} is not active. Skipping...')
            inactive.add(name)
            continue

        in_config.add(name)
        if not _load_module(name):
            raise ValueError(f"Couldn't find module {name} under modules directory")

        log.info(f'Module {name} is loaded')
    return in_config, inactive


def _get_modules_from_config():
    try:
        modules = config.get_property('modules')
    except KeyError as e:
        raise KeyError('"modules" has not been found in the config file. Nothing to load') from e

    log.info('Found %d modules that have been found in the config', len(modules))
    return modules


def _load_module(name: str):
    """
    Loads a module but not initializing it
    """
    try:
        importlib.import_module(f'{_MODULE_PREFIX}.{name}')  # nosemgrep
        # semgrep finding ignored as no upstream user input is passed to the import_module function
        # Only code admins will have access to the parameters of the f-string
        return True
    except ModuleNotFoundError as e:
        log.error(f"Couldn't load module due to: {e}")
        return False


def _initialize_modules(modes: Set[ImportMode]):
    """
    Initialize all modules for supported modes. This method is using topological sorting for a graph of module
    dependencies. It's needed to load module in a specific order: first modules to load are without dependencies.
    It might help to avoid possible issues if there is a load in the module constructor (which can be the case
    if a module supports a few importing modes).
    """
    modules = _all_modules()
    dependencies = defaultdict(list)
    degrees = defaultdict(int)
    supported = []
    for module in modules:
        if module.is_supported(modes):
            supported.append(module)
            degrees[module] += len(module.depends_on())
            for dependency in module.depends_on():
                dependencies[dependency].append(module)

    queue = deque()
    for module in supported:
        if degrees[module] == 0:
            queue.append(module)

    initialized = 0
    while queue:
        to_init = queue.popleft()
        _initialize_module(to_init)
        initialized += 1

        for dependant in dependencies[to_init]:
            degrees[dependant] -= 1
            if degrees[dependant] == 0:
                queue.append(dependant)

    if initialized < len(degrees):
        # Happens if the ModuleInterface for dependency doesn't support import mode
        # The case when there is circular imports should already be covered by python loader
        raise ImportError('Not all modules have been initialized. Check if your import modes are correct')


def _get_module_name(module):
    return module[len(_MODULE_PREFIX) + 1 :].split('.')[0]  # gets only top level module name


def _initialize_module(module: Type[ModuleInterface]):
    module()  # call a constructor for initialization
    _LOADED_MODULES.add(module.name())


def _check_loading_correct(in_config: Set[str], modes: Set[ImportMode]):
    """
    To avoid unintentional loading (without ModuleInterface) we can check all loaded modules.
    Unintentional/incorrect loading might happen if module A has a direct reference to module B without declaring it
    in ModuleInterface. Doing so, this might lead to a problem when a module interface require to load something during
    initialization. But since ModuleInterface is not initializing properly (using depends_on)
    some functionality may work wrongly.
    """
    expected_load = set()
    # 1) Adds all modules to load
    for module in _all_modules():
        if module.is_supported(modes) and module.name() in in_config:
            expected_load.add(module)

    # 2) Add all dependencies
    to_add = list(expected_load)
    while to_add:
        new_to_add = []
        while to_add:
            module = to_add.pop()
            for dependency in module.depends_on():
                if dependency not in expected_load:
                    expected_load.add(dependency)
                    if not dependency.is_supported(modes):
                        raise ImportError(f"Dependency {dependency.name()} doesn't support {modes}")

                    new_to_add.append(dependency)
        to_add = new_to_add

    # 3) Checks all found ModuleInterfaces
    for module in _all_modules():
        if module.is_supported(modes) and module not in expected_load:
            raise ImportError(
                f'ModuleInterface has not been initialized for module {module.name()}. Declare the module in depends_on'
            )

    # 4) Checks all references for modules (when ModuleInterfaces don't exist or not supported)
    checked_module_names = {module.name() for module in expected_load}
    # Modules from the config that doesn't support the current mode weren't added in Step1, adding them here
    checked_module_names |= in_config
    for module in sys.modules.keys():
        if module.startswith(_MODULE_PREFIX) and module != __name__:  # skip loader
            name = _get_module_name(module)
            if name and name not in checked_module_names:
                raise ImportError(f"The package {module} has been imported, but it doesn't contain ModuleInterface")


def _describe_loading(in_config: Set[str], inactive: Set[str]):
    modules = _all_modules()
    for module in modules:
        name = module.name()
        log.debug(f'The {name} module was loaded')
        if name in inactive:
            log.info(
                f"There is a module that depends on {module.name()}. The module has been loaded despite it's inactive."
            )
        elif name not in in_config:
            log.info(
                f'There is a module that depends on {module.name()}. '
                "The module has been loaded despite it's not specified in the configuration file."
            )


def _remove_module_prefix(module: str):
    if module.startswith(_MODULE_PREFIX):
        return module[len(_MODULE_PREFIX) + 1 :]
    raise ValueError(f'Module  {module} should always starts with {_MODULE_PREFIX}')


def _all_modules():
    return ModuleInterface.__subclasses__()
