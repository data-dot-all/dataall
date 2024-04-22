from abc import ABC
from typing import List, Type, Set

import pytest

from dataall.base.loader import ModuleInterface, ImportMode
from dataall.base import loader

order = []


class TestModule(ModuleInterface, ABC):
    def __init__(self):
        order.append(self.__class__)

    @classmethod
    def name(cls) -> str:
        return cls.__name__


class TestApiModule(TestModule):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes


class AModule(TestApiModule):
    pass


class BModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [AModule]


class CModule(TestModule):
    @staticmethod
    def is_supported(modes: List[ImportMode]) -> bool:
        return ImportMode.CDK in modes


class DModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [BModule]


class EModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [BModule]


class FModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [EModule]


class GModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [AModule, BModule]


class IModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [EModule, DModule]


class JModule(TestApiModule):
    pass


class KModule(TestApiModule):
    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [JModule, EModule]


@pytest.fixture(scope='module', autouse=True)
def patch_prefix():
    prefix = loader._MODULE_PREFIX
    loader._MODULE_PREFIX = 'tests.modules.test_loader'
    yield

    loader._MODULE_PREFIX = prefix


@pytest.fixture(scope='function', autouse=True)
def clean_order():
    yield
    order.clear()


def patch_loading(mocker, all_modules, in_config):
    mocker.patch(
        'dataall.base.loader._all_modules',
        return_value=all_modules,
    )
    mocker.patch('dataall.base.loader._load_modules', return_value=({module.name() for module in in_config}, {}))


@pytest.fixture(scope='function', autouse=True)
def patch_modes(mocker):
    mocker.patch('dataall.base.loader._ACTIVE_MODES', set())
    yield


def test_nothing_to_load(mocker):
    patch_loading(mocker, [], set())
    loader.load_modules({ImportMode.API, ImportMode.CDK})
    assert len(order) == 0


def test_import_with_one_dependency(mocker):
    patch_loading(mocker, [AModule, BModule], {BModule})
    loader.load_modules({ImportMode.API})
    assert order == [AModule, BModule]


def test_load_with_cdk_mode(mocker):
    patch_loading(mocker, [DModule, CModule, BModule], {CModule})
    loader.load_modules({ImportMode.CDK})
    assert order == [CModule]


def test_many_nested_layers(mocker):
    patch_loading(mocker, [BModule, CModule, AModule, DModule], {DModule, CModule})
    loader.load_modules({ImportMode.API})
    correct_order = [AModule, BModule, DModule]
    assert order == correct_order
    assert CModule not in correct_order


def test_complex_loading(mocker):
    patch_loading(
        mocker,
        [AModule, BModule, CModule, DModule, EModule, FModule, GModule, IModule, JModule, KModule],
        {CModule, FModule, GModule, IModule, KModule},
    )

    loader.load_modules({ImportMode.API})
    assert order == [AModule, JModule, BModule, DModule, EModule, GModule, FModule, IModule, KModule]


def test_incorrect_loading(mocker):
    patch_loading(mocker, [CModule], set())  # A is not specified in config, but was found
    with pytest.raises(ImportError):
        loader.load_modules({ImportMode.CDK})

    patch_loading(mocker, [AModule, BModule], {AModule})
    with pytest.raises(ImportError):
        loader.load_modules({ImportMode.API})
