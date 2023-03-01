from dataall.modules.loader import load_modules, ImportMode
import sys

modules = ["dataall.modules.notebooks"]


def test_loader_imported_modules():
    load_modules(modes=[ImportMode.API, ImportMode.TASKS])

    for module in modules:
        assert module in sys.modules

        assert f"{module}.gql" in sys.modules
        assert f"{module}.cdk" not in sys.modules
        assert f"{module}.tasks" in sys.modules

