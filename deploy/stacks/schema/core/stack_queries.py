from functools import cache

from awscdk.appsync_utils import ResolvableField, GraphqlType

from stacks.appsync import AppSyncStack
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.stack_types import StackTypes


@cache
class StackQueries:
    def __init__(
        self,
        app_sync_stack: AppSyncStack,
        env_types: EnvironmentTypes,
        stack_types: StackTypes,
        **_kwargs,
    ):
        self.get_stack = ResolvableField(
            return_type=stack_types.stack.attribute(),
            args={'environmentUri': GraphqlType.string(), 'stackUri': GraphqlType.string()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('getStack', self.get_stack)
        env_types.environment.add_field(field_name='stack', field=self.get_stack)

        self.get_stack_logs = ResolvableField(
            return_type=stack_types.stack_log.attribute(is_list=True),
            args={'environmentUri': GraphqlType.string(), 'stackUri': GraphqlType.string()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('getStackLogs', self.get_stack_logs)
