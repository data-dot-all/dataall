from typing import Protocol, List


class GroupResource(Protocol):
    def count_resources(self, session, environment_uri, group_uri) -> int:
        ...


class GroupResourceManager:
    """
    API for managing group resources
    """
    _resources: List[GroupResource] = []

    @staticmethod
    def register(resource: GroupResource):
        GroupResourceManager._resources.append(resource)

    @staticmethod
    def count_group_resources(session, environment_uri, group_uri) -> int:
        counter = 0
        for resource in GroupResourceManager._resources:
            counter += resource.count_resources(session, environment_uri, group_uri)
        return counter
