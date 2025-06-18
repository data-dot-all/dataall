from dataclasses import dataclass
from typing import Type, Dict, Optional, Protocol, Union

from dataall.base.api import gql
from dataall.base.api.gql.graphql_union_type import UnionTypeRegistry
from dataall.base.db import Resource
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer


class Identifiable(Protocol):
    @classmethod
    def uri_column(cls): ...


@dataclass
class GlossaryDefinition:
    """Glossary's definition used for registration references of other modules"""

    target_type: str
    object_type: str
    model: Union[Type[Resource], Identifiable]  # should be an intersection, but python typing doesn't have one yet
    reindexer: Type[BaseIndexer] = None  # a callback to reindex glossaries in open search

    def target_uri(self):
        return self.model.uri_column()


class GlossaryRegistry(UnionTypeRegistry):
    """Registry of glossary definition and API to retrieve and reindex data"""

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

    @classmethod
    def types(cls):
        return [gql.Ref(definition.object_type) for definition in cls._DEFINITIONS.values()]

    @classmethod
    def reindex(cls, session, target_type: str, target_uri: str):
        definition = cls._DEFINITIONS[target_type]
        if definition.reindexer:
            definition.reindexer.upsert(session, target_uri)
