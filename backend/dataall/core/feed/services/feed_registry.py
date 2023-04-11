from dataclasses import dataclass
from typing import Dict, Type
from dataall.db import Resource, models


@dataclass
class FeedDefinition:
    target_type: str
    model: Type[Resource]


class FeedRegistry:
    """Registers feeds for different models"""
    _DEFINITION: Dict[str, FeedDefinition] = {}

    @classmethod
    def register(cls, feed: FeedDefinition):
        cls._DEFINITION[feed.target_type] = feed

    @classmethod
    def find(cls, target_type: str):
        return cls._DEFINITION[target_type]

    @classmethod
    def find_by_model(cls, obj: Resource):
        for target_type, feed in cls._DEFINITION.items():
            if isinstance(obj, feed.model):
                return target_type
        return None


FeedRegistry.register(FeedDefinition("Worksheet", models.Worksheet))
FeedRegistry.register(FeedDefinition("DataPipeline", models.DataPipeline))
FeedRegistry.register(FeedDefinition("DatasetTable", models.DatasetTable))
FeedRegistry.register(FeedDefinition("DatasetStorageLocation", models.DatasetStorageLocation))
FeedRegistry.register(FeedDefinition("Dashboard", models.Dashboard))
