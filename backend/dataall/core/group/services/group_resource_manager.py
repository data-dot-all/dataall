from abc import ABC
from typing import List


class EnvironmentResource(ABC):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        raise NotImplementedError()

    @staticmethod
    def delete_env(session, environment):
        pass


class EnvironmentResourceManager:
    """
    API for managing group resources
    """
    _resources: List[EnvironmentResource] = []

    @staticmethod
    def register(resource: EnvironmentResource):
        EnvironmentResourceManager._resources.append(resource)

    @staticmethod
    def count_group_resources(session, environment, group_uri) -> int:
        counter = 0
        for resource in EnvironmentResourceManager._resources:
            counter += resource.count_resources(session, environment, group_uri)
        return counter

    @staticmethod
    def delete_env(session, environment):
        for resource in EnvironmentResourceManager._resources:
            resource.delete_env(session, environment)

