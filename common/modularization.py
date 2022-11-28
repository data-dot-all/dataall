from abc import ABC, abstractmethod
from enum import Enum


class ApplicationComponents(Enum):
    GRAPHQL = "graphql_api"
    ECS = "ecs_tasks"

class Core(ABC):

    @abstractmethod
    def define_graphql_api(self):
        pass

class Module(ABC):

    @abstractmethod
    def define_graphql_api(self):
        pass
