from backend.api.gql._cache import cache_instances
from backend.api.gql.graphql_field import Field


@cache_instances
class MutationField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
