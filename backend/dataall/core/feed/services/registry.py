from dataclasses import dataclass
from typing import Type, Dict

from dataall.db import Resource, models


@dataclass
class FeedDefinition:
    target_type: str
    model: Type[Resource]


class FeedRegistry:
    """Registers models for different target types"""

    def __init__(self):
        self._definitions: Dict[str, FeedDefinition] = {}

    def register(self, model: FeedDefinition):
        self._definitions[model.target_type] = model

    def find(self, target_type: str):
        return self._definitions[target_type]

    def find_by_model(self, obj: Resource):
        for target_type, definition in self._definitions.items():
            if isinstance(obj, definition.model):
                return target_type
        return None


FeedRegistry.register(FeedDefinition("Worksheet", models.Worksheet))
FeedRegistry.register(FeedDefinition("DataPipeline", models.DataPipeline))
FeedRegistry.register(FeedDefinition("DatasetTable", models.DatasetTable))
FeedRegistry.register(FeedDefinition("DatasetStorageLocation", models.DatasetStorageLocation))
FeedRegistry.register(FeedDefinition("Dashboard", models.Dashboard))
