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

    def get_property(self, key: str, default=None) -> Any:
        """
        Retrieves a copy of the property
        Config uses dot as a separator to navigate easy to the needed property e.g.
        some.needed.parameter is equivalent of config["some"]["needed"]["parameter"]
        It enables fast navigation for any nested parameter
        """
        res = self._config

        props = key.split(".")

        # going through the hierarchy of json
        for prop in props:
            if prop not in res:
                if default is not None:
                    return default

                raise KeyError(f"Couldn't find a property {key} in the config")

            res = res[prop]
        return copy.deepcopy(res)

    def set_property(self, key: str, value: Any) -> None:
        """
        Sets a property into the config
        If the property has dot it will be split to nested levels
        """
        conf = self._config
        props = key.split(".")

        for i, prop in enumerate(props):
            if i == len(props) - 1:
                conf[prop] = value
            else:
                conf[prop] = conf[prop] if prop in conf is not None else {}
                conf = conf[prop]

    @staticmethod
    def _read_config_file() -> Dict[str, Any]:
        with open(_Config._path_to_file()) as config_file:
            return json.load(config_file)

    @staticmethod
    def _path_to_file() -> str:
        """Tries to get a property. If not defined it tries to resolve the config from the current file's directory"""
        path = os.getenv("config_location")
        if path:
            return path
        return os.path.join(Path(__file__).parents[3], "config.json")

    def __repr__(self):
        return str(self._config)


config = _Config()
