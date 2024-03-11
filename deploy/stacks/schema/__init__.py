import importlib
import pkgutil
from typing import List

from injector import Injector, Module

from stacks import schema


class SchemaBase(object):
    pass


def import_submodules(package):
    """ Import all submodules of a module, recursively, including subpackages
    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if is_pkg:
            results.update(import_submodules(full_name))
    return results


def create_schema(modules: List[Module]):
    """
    1. Recursively import all submodules under 'schema' to ensure that __subclasses__ will list all the classes that inherit from SchemaBase.
    2. Force injector initialise all the classes that inherit from SchemaBase
    """
    injector = Injector(modules)
    import_submodules(schema)
    for cls in SchemaBase.__subclasses__():
        injector.get(cls)
