from dataclasses import dataclass
from typing import Type, Dict

from dataall.api import gql
from dataall.api.gql.graphql_union_type import UnionTypeRegistry
from dataall.db import Resource, models


@dataclass
class FeedDefinition:
    target_type: str
    model: Type[Resource]


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
    def find_target(cls, obj: Resource):
        for target_type, definition in cls._DEFINITIONS.items():
            if isinstance(obj, definition.model):
                return target_type
        return None

    @classmethod
    def types(cls):
        return [gql.Ref(target_type) for target_type in cls._DEFINITIONS.keys()]


FeedRegistry.register(FeedDefinition("Worksheet", models.Worksheet))
FeedRegistry.register(FeedDefinition("DataPipeline", models.DataPipeline))
FeedRegistry.register(FeedDefinition("DatasetTable", models.DatasetTable))
FeedRegistry.register(FeedDefinition("Dashboard", models.Dashboard))
