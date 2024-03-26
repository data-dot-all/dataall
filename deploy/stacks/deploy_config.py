"""Reads and encapsulates the configuration provided in config.json"""

import json
import copy
from typing import Any, Dict
import os
from pathlib import Path


class _DeployConfig:
    """A container of properties in the configuration file
    and any other that can be specified/overwritten later in the application"""

    def __init__(self):
        self._config = self._read_config_file()
        self._version = self._read_version_file()

    def get_dataall_version(self) -> str:
        return json.dumps(self._version)

    def get_property(self, key: str, default=None) -> Any:
        """
        Retrieves a copy of the property
        Config uses dot as a separator to navigate easy to the needed property e.g.
        some.needed.parameter is equivalent of config["some"]["needed"]["parameter"]
        It enables fast navigation for any nested parameter
        """
        res = self._config

        props = key.split('.')

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
        props = key.split('.')

        for i, prop in enumerate(props):
            if i == len(props) - 1:
                conf[prop] = value
            else:
                conf[prop] = conf[prop] if prop in conf is not None else {}
                conf = conf[prop]

    @classmethod
    def _read_config_file(cls) -> Dict[str, Any]:
        with open(cls._path_to_file('config.json')) as config_file:
            return json.load(config_file)

    @classmethod
    def _read_version_file(cls) -> Dict[str, Any]:
        with open(cls._path_to_file('version.json')) as version_file:
            return json.load(version_file)

    @staticmethod
    def _path_to_file(filename) -> str:
        """Tries to get a property. If not defined it tries to resolve the config from the current file's directory"""
        path = os.getenv('config_location')
        if path:
            return path
        return os.path.join(Path(__file__).parents[2], filename)

    def __repr__(self):
        return str(self._config)


deploy_config = _DeployConfig()
