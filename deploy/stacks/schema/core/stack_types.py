from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import GraphqlType, EnumType, CodeFirstSchema, ObjectType
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes


@singleton
class StackTypes(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            common_types: CommonTypes,
    ):
        schema: CodeFirstSchema = api.schema

        self.stack_log = ObjectType('StackLog', definition={
            'logStream': GraphqlType.string(),
            'logGroup': GraphqlType.string(),
            'timestamp': GraphqlType.string(),
            'message': GraphqlType.string(),
        })
        schema.add_type(self.stack_log)

        self.stack = ObjectType('Stack', definition={
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
        })
        schema.add_type(self.stack)
