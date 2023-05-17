from abc import ABC
from typing import List


class GroupResource(ABC):
    def count_resources(self, session, environment, group_uri) -> int:
        raise NotImplementedError()


class GroupResourceManager:
    """
    API for managing group resources
    """
    _resources: List[GroupResource] = []

    @staticmethod
    def register(resource: GroupResource):
        GroupResourceManager._resources.append(resource)

    @staticmethod
    def count_group_resources(session, environment, group_uri) -> int:
        counter = 0
        for resource in GroupResourceManager._resources:
            counter += resource.count_resources(session, environment, group_uri)
        return counter
