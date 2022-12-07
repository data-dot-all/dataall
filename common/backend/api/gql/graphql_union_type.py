from common.api.gql._cache import cache_instances
from common.api.gql.utils import get_named_type


@cache_instances
class Union:
    _register = {}

    def __init__(self, name, types=[], resolver=lambda *_, **__: None):
        self.name = name
        self.types = types
        self.resolver = resolver
        Union._register[name] = self

    def gql(self, *args, **kwargs):
        return f"union {self.name} = {'|'.join([get_named_type(t).name for t in self.types])}"


if __name__ == '__main__':
    from .. import gql

    User = gql.ObjectType(name='User', fields=[])

    Group = gql.ObjectType(name='Group', fields=[])
    userorgroup = Union(name='userorgroup', types=[gql.Thunk(lambda: User), Group])

    print(userorgroup.gql())
