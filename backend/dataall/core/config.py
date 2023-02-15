"""Reads and encapsulates the configuration provided in config.json"""
import json
import copy
from typing import Any, Dict


class _Config:
    """A container of properties in the configuration file
     and any other that can be specified/overwritten later in the application"""

    _CONFIG_PATH = "../config.json"

    def __init__(self):
        self._config = self._read_config_file()

    def get_property(self, key: str) -> Any:
        if key not in self._config:
            raise KeyError

        return copy.deepcopy(self._config[key])

    def set_property(self, key: str, value: Any) -> None:
        if key not in self._config:
            raise KeyError

        self._config[key] = value

    def _read_config_file(self) -> Dict[str, Any]:
        with open(self._CONFIG_PATH) as config_file:
            return json.load(config_file)


    def __repr__(self):
        return str(self._config)


config = _Config()