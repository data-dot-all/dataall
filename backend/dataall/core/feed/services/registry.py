from dataclasses import dataclass
from typing import Type, Dict

from dataall.db import Resource, models


@dataclass
class FeedDefinition:
    target_type: str
    model: Type[Resource]


class FeedRegistry:
    """Registers models for different target types"""
    _DEFINITIONS: Dict[str, FeedDefinition] = {}

    @classmethod
    def register(cls, model: FeedDefinition):
        cls._DEFINITIONS[model.target_type] = model

    @classmethod
    def find(cls, target_type: str):
        return cls._DEFINITIONS[target_type]

    @classmethod
    def find_by_model(cls, obj: Resource):
        for target_type, definition in cls._DEFINITIONS.items():
            if isinstance(obj, definition.model):
                return target_type
        return None


FeedRegistry.register(FeedDefinition("Worksheet", models.Worksheet))
FeedRegistry.register(FeedDefinition("DataPipeline", models.DataPipeline))
FeedRegistry.register(FeedDefinition("DatasetTable", models.DatasetTable))
FeedRegistry.register(FeedDefinition("DatasetStorageLocation", models.DatasetStorageLocation))
FeedRegistry.register(FeedDefinition("Dashboard", models.Dashboard))
