from ._cache import cache_instances
from .graphql_field import Field


@cache_instances
class QueryField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
