from dataclasses import dataclass
from typing import Type, Dict

from dataall.db import Resource, models


@dataclass
class ModelDefinition:
    target_type: str
    model: Type[Resource]


class ModelRegistry:
    """Registers models for different target types"""

    def __init__(self):
        self._definitions: Dict[str, ModelDefinition] = {}

    def register(self, model: ModelDefinition):
        self._definitions[model.target_type] = model

    def find(self, target_type: str):
        return self._definitions[target_type]

    def find_by_model(self, obj: Resource):
        for target_type, definition in self._definitions.items():
            if isinstance(obj, definition.model):
                return target_type
        return None


# TODO should migrate to a proper file after the modularization
FeedRegistry = ModelRegistry()
GlossaryRegistry = ModelRegistry()


FeedRegistry.register(ModelDefinition("Worksheet", models.Worksheet))
FeedRegistry.register(ModelDefinition("DataPipeline", models.DataPipeline))
FeedRegistry.register(ModelDefinition("DatasetTable", models.DatasetTable))
FeedRegistry.register(ModelDefinition("DatasetStorageLocation", models.DatasetStorageLocation))
FeedRegistry.register(ModelDefinition("Dashboard", models.Dashboard))

GlossaryRegistry.register(ModelDefinition("DatasetTable", models.DatasetTable))
GlossaryRegistry.register(ModelDefinition("DatasetStorageLocation", models.DatasetStorageLocation))
GlossaryRegistry.register(ModelDefinition("Dashboard", models.Dashboard))
GlossaryRegistry.register(ModelDefinition("DatasetTable", models.DatasetTable))
GlossaryRegistry.register(ModelDefinition("Dataset", models.Dataset))
