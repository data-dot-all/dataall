from dataall.modules.loader import load_modules
import sys

modules = ["dataall.modules.notebooks"]


def test_loader_imported_modules():
    load_modules()

    for module in modules:
        assert module in sys.modules

