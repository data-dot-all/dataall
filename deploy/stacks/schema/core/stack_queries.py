from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import CodeFirstSchema, ResolvableField, GraphqlType
from injector import inject, singleton

from stacks.appsync import AppSyncStack
from stacks.schema import SchemaBase
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.stack_types import StackTypes


@singleton
class StackQueries(SchemaBase):
    @inject
    def __init__(
        self,
        env_types=EnvironmentTypes(),
        stack_types=StackTypes(),
    ):
        schema = AppSyncStack.INSTANCE.schema
        data_source = AppSyncStack.INSTANCE.data_source

        self.get_stack = ResolvableField(
            return_type=stack_types.stack.attribute(),
            args={'environmentUri': GraphqlType.string(), 'stackUri': GraphqlType.string()},
            data_source=data_source,
        )
        schema.add_query('getStack', self.get_stack)
        env_types.environment.add_field(field_name='stack', field=self.get_stack)

        self.get_stack_logs = ResolvableField(
            return_type=stack_types.stack_log.attribute(is_list=True),
            args={'environmentUri': GraphqlType.string(), 'stackUri': GraphqlType.string()},
            data_source=data_source,
        )
        schema.add_query('getStackLogs', self.get_stack_logs)
