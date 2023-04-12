from dataclasses import dataclass
from typing import Type, Dict, Optional, Protocol, Union

from dataall.db import Resource, models


class Identifiable(Protocol):
    def uri(self):
        ...


@dataclass
class GlossaryDefinition:
    target_type: str
    object_type: str
    model: Union[Type[Resource], Identifiable]  # should be an intersection, but python typing doesn't have one yet

    def target_uri(self):
        return self.model.uri()


class GlossaryRegistry:
    _DEFINITIONS: Dict[str, GlossaryDefinition] = {}

    @classmethod
    def register(cls, glossary: GlossaryDefinition) -> None:
        cls._DEFINITIONS[glossary.target_type] = glossary

    @classmethod
    def find_model(cls, target_type: str) -> Optional[Resource]:
        definition = cls._DEFINITIONS[target_type]
        return definition.model if definition is not None else None

    @classmethod
    def find_object_type(cls, model: Resource) -> Optional[str]:
        for _, definition in cls._DEFINITIONS.items():
            if isinstance(model, definition.model):
                return definition.object_type
        return None

    @classmethod
    def definitions(cls):
        return cls._DEFINITIONS.values()


GlossaryRegistry.register(GlossaryDefinition("DatasetTable", "DatasetTable", models.DatasetTable))
GlossaryRegistry.register(GlossaryDefinition("Folder", "DatasetStorageLocation", models.DatasetStorageLocation))
GlossaryRegistry.register(GlossaryDefinition("Dashboard", "Dashboard", models.Dashboard))
GlossaryRegistry.register(GlossaryDefinition("DatasetTable", "DatasetTable", models.DatasetTable))
GlossaryRegistry.register(GlossaryDefinition("Dataset", "Dataset", models.Dataset))
