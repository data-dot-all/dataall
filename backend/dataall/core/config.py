"""Reads and encapsulates the configuration provided in config.json"""
import json
import copy
from typing import Any, Dict
import os
from pathlib import Path

class _Config:
    """A container of properties in the configuration file
     and any other that can be specified/overwritten later in the application"""

    def __init__(self):
        self._config = _Config._read_config_file()

    def get_property(self, key: str) -> Any:
        """Retrieves a copy of the property"""
        if key not in self._config:
            raise KeyError(f"Couldn't find a property {key} in the config")

        return copy.deepcopy(self._config[key])

    def set_property(self, key: str, value: Any) -> None:
        """Sets a property into the config"""
        self._config[key] = value

    @staticmethod
    def _read_config_file() -> Dict[str, Any]:
        with open(_Config._path_to_file()) as config_file:
            return json.load(config_file)

    @staticmethod
    def _path_to_file() -> str:
        """Tries to get a property. If not defined it tries to resolve the config from the current file's directory"""
        path = os.getenv( "config_location")
        if path:
            return path
        return os.path.join(Path(__file__).parents[3], "config.json")

    def __repr__(self):
        return str(self._config)


config = _Config()
