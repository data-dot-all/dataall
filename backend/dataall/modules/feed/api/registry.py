from dataclasses import dataclass
from typing import Type, Dict

from dataall.base.api import gql
from dataall.base.api.gql.graphql_union_type import UnionTypeRegistry
from dataall.base.db import Resource


@dataclass
class FeedDefinition:
    target_type: str
    model: Type[Resource]
    permission: str


class FeedRegistry(UnionTypeRegistry):
    """Registers models for different target types"""

    _DEFINITIONS: Dict[str, FeedDefinition] = {}

    @classmethod
    def register(cls, definition: FeedDefinition):
        cls._DEFINITIONS[definition.target_type] = definition

    @classmethod
    def find_model(cls, target_type: str):
        return cls._DEFINITIONS[target_type].model

    @classmethod
    def find_permission(cls, target_type: str):
        return cls._DEFINITIONS[target_type].permission

    @classmethod
    def find_target(cls, obj: Resource):
        for target_type, definition in cls._DEFINITIONS.items():
            if isinstance(obj, definition.model):
                return target_type
        return None

    @classmethod
    def types(cls):
        return [gql.Ref(target_type) for target_type in cls._DEFINITIONS.keys()]
