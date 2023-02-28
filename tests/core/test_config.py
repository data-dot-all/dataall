from dataall.core.config import config


def test_config():
    """Checks that properties are read correctly"""
    modules = config.get_property("modules")
    assert "notebooks" in modules
