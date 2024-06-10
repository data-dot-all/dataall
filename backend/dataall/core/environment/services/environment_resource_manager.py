from abc import ABC
from typing import List
from dataall.base.context import get_context


class EnvironmentResource(ABC):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return 0

    @staticmethod
    def delete_env(session, environment):
        pass

    @staticmethod
    def create_env(session, environment, **kwargs):
        pass

    @staticmethod
    def update_env(session, environment, **kwargs):
        return False

    @staticmethod
    def count_role_resources(session, role_uri):
        return 0


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
    def deploy_updated_stack(cls, prev_prefix, environment, **kwargs):
        deploy_stack = prev_prefix != environment.resourcePrefix
        with get_context().db_engine.scoped_session() as session:
            for resource in cls._resources:
                deploy_stack |= resource.update_env(session, environment, **kwargs)

            return deploy_stack

    @classmethod
    def delete_env(cls, session, environment):
        for resource in cls._resources:
            resource.delete_env(session, environment)

    @classmethod
    def create_env(cls, session, environment, **kwargs):
        for resource in cls._resources:
            resource.create_env(session, environment, **kwargs)

    @classmethod
    def count_consumption_role_resources(cls, session, role_uri):
        counter = 0
        for resource in cls._resources:
            counter += resource.count_role_resources(session, role_uri)
        return counter
