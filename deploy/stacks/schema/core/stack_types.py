from functools import cache

from awscdk.appsync_utils import GraphqlType, ObjectType

from stacks.appsync import AppSyncStack
from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes


@cache
class StackTypes(SchemaBase):
    def __init__(
        self,
        common_types=CommonTypes(),
    ):
        schema = AppSyncStack.INSTANCE.schema
        data_source = AppSyncStack.INSTANCE.data_source

        self.stack_log = ObjectType(
            'StackLog',
            definition={
                'logStream': GraphqlType.string(),
                'logGroup': GraphqlType.string(),
                'timestamp': GraphqlType.string(),
                'message': GraphqlType.string(),
            },
        )
        schema.add_type(self.stack_log)

        self.stack = ObjectType(
            'Stack',
            definition={
                'stackUri': GraphqlType.id(),
                'targetUri': GraphqlType.string(is_required=True),
                'stack': GraphqlType.string(is_required=True),
                'environmentUri': GraphqlType.string(),
                'name': GraphqlType.string(),
                'accountid': GraphqlType.string(is_required=True),
                'region': GraphqlType.string(is_required=True),
                'status': GraphqlType.string(),
                'stackid': GraphqlType.string(),
                'link': GraphqlType.string(),
                'outputs': GraphqlType.string(),
                'resources': GraphqlType.string(),
                'error': GraphqlType.string(),
                'events': GraphqlType.string(),
                'EcsTaskArn': GraphqlType.string(),
                'EcsTaskId': GraphqlType.string(),
            },
        )
        schema.add_type(self.stack)
