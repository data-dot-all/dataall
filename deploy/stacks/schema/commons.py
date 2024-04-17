from awscdk.appsync_utils import EnumType, InterfaceType, GraphqlType

from stacks.appsync import AppSyncStack


class CommonTypes:
    def __init__(self, app_sync_stack: AppSyncStack):
        self.sort_direction = EnumType(
            'SortDirection',
            definition=[
                'asc',
                'desc',
            ],
        )
        app_sync_stack.schema.add_type(self.sort_direction)

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
        app_sync_stack.schema.add_type(self.paged_result)

        self.filter_args = {
            'term': GraphqlType.string(),
            'displayArchived': GraphqlType.boolean(),
            'page': GraphqlType.int(),
            'pageSize': GraphqlType.int(),
            'tags': GraphqlType.string(is_list=True),
        }
