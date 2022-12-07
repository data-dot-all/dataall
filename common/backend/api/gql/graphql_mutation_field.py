from common.api.gql._cache import cache_instances
from common.api.gql.graphql_field import Field


@cache_instances
class MutationField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
