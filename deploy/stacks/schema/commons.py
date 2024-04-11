from functools import cache

from awscdk.appsync_utils import EnumType, InterfaceType, GraphqlType

from stacks.appsync import AppSyncStack
from stacks.schema import SchemaBase


@cache
class CommonTypes(SchemaBase):
    def __init__(self):
        schema = AppSyncStack.INSTANCE.schema

        self.sort_direction = EnumType(
            'SortDirection',
            definition=[
                'asc',
                'desc',
            ],
        )
        schema.add_type(self.sort_direction)

        self.paged_result = InterfaceType(
            'PagedResult',
            definition={
                'count': GraphqlType.int(),
                'pageSize': GraphqlType.int(),
                'nextPage': GraphqlType.int(),
                'pages': GraphqlType.int(),
                'page': GraphqlType.int(),
                'previousPage': GraphqlType.int(),
                'hasNext': GraphqlType.boolean(),
                'hasPrevious': GraphqlType.boolean(),
                'count': GraphqlType.int(),  # noqa
            },
        )
        schema.add_type(self.paged_result)

        self.filter_args = {
            'term': GraphqlType.string(),
            'displayArchived': GraphqlType.boolean(),
            'page': GraphqlType.int(),
            'pageSize': GraphqlType.int(),
            'tags': GraphqlType.string(is_list=True),
        }
