from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import CodeFirstSchema, EnumType, InterfaceType, GraphqlType
from injector import singleton, inject

from stacks.schema import SchemaBase


@singleton
class CommonTypes(SchemaBase):
    @inject
    def __init__(self, api: GraphqlApi):
        schema: CodeFirstSchema = api.schema

        self.sort_direction = EnumType('SortDirection', definition=[
            'asc',
            'desc',
        ])
        schema.add_type(self.sort_direction)

        self.paged_result = InterfaceType('PagedResult', definition={
            'count': GraphqlType.int(),
            'pageSize': GraphqlType.int(),
            'nextPage': GraphqlType.int(),
            'pages': GraphqlType.int(),
            'page': GraphqlType.int(),
            'previousPage': GraphqlType.int(),
            'hasNext': GraphqlType.boolean(),
            'hasPrevious': GraphqlType.boolean(),
            'count': GraphqlType.int(),
        })
        schema.add_type(self.paged_result)

        self.filter_args = {
            'term': GraphqlType.string(),
            'displayArchived': GraphqlType.boolean(),
            'page': GraphqlType.int(),
            'pageSize': GraphqlType.int(),
            'tags': GraphqlType.string(is_list=True),
        }
