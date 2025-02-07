from abc import ABC

from ._cache import cache_instances
from .utils import get_named_type


class UnionTypeRegistry(ABC):
    """An abstract class that is used to provide union type in runtime"""

    @classmethod
    def types(cls):
        raise NotImplementedError('Types method is not implemented')


@cache_instances
class Union:
    _register = {}

    def __init__(self, name, types=[], type_registry=None, resolver=lambda *_, **__: None):
        self.name = name
        self.types = types
        self.type_registry = type_registry
        self.resolver = resolver
        Union._register[name] = self

    def gql(self, *args, **kwargs):
        types = self.type_registry.types() if self.type_registry else self.types
        return f'union {self.name} = {"|".join([get_named_type(t).name for t in types])}'


if __name__ == '__main__':
    from dataall.base.api import gql

    User = gql.ObjectType(name='User', fields=[])

    Group = gql.ObjectType(name='Group', fields=[])
    userorgroup = Union(name='userorgroup', types=[gql.Thunk(lambda: User), Group])

    print(userorgroup.gql())
