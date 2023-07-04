from abc import ABC
from typing import List

from dataall.api.Objects.Stack import stack_helper


class EnvironmentResource(ABC):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return 0

    @staticmethod
    def delete_env(session, environment):
        pass

    @staticmethod
    def update_env(session, environment):
        pass


class EnvironmentResourceManager:
    """
    API for managing environment and environment group lifecycle.
    Contains callbacks that are invoked when something is happened with the environment.
    """
    _resources: List[EnvironmentResource] = []

    @classmethod
    def register(cls, resource: EnvironmentResource):
        cls._resources.append(resource)

    @classmethod
    def count_group_resources(cls, session, environment, group_uri) -> int:
        counter = 0
        for resource in cls._resources:
            counter += resource.count_resources(session, environment, group_uri)
        return counter

    @classmethod
    def deploy_updated_stack(cls, session, prev_prefix, environment):
        deploy_stack = prev_prefix != environment.resourcePrefix
        for resource in cls._resources:
            deploy_stack |= resource.update_env(session, environment)

        if deploy_stack:
            stack_helper.deploy_stack(targetUri=environment.environmentUri)

    @classmethod
    def delete_env(cls, session, environment):
        for resource in cls._resources:
            resource.delete_env(session, environment)
