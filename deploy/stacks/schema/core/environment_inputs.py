from functools import cache

from awscdk.appsync_utils import InputType

from stacks.appsync import AppSyncStack
from stacks.schema.commons import CommonTypes
from stacks.schema.core.environment_types import EnvironmentTypes


@cache
class EnvironmentInputs:
    def __init__(
        self,
        app_sync_stack: AppSyncStack,
        common_types: CommonTypes,
        env_types: EnvironmentTypes,
        **_kwargs,
    ):
        environment_sort_criteria = InputType(
            'EnvironmentSortCriteria',
            definition={
                'field': env_types.environment_sort_field.attribute(),
                'direction': common_types.sort_direction.attribute(),
            },
        )
        app_sync_stack.schema.add_type(environment_sort_criteria)

        self.environment_filter = InputType(
            'EnvironmentFilter',
            definition={
                **common_types.filter_args,
                'roles': env_types.environment_permission.attribute(is_list=True),
                'sort': environment_sort_criteria.attribute(is_list=True),
            },
        )
        app_sync_stack.schema.add_type(self.environment_filter)

        self.vpc_filter = InputType(
            'VpcFilter',
            definition={
                **common_types.filter_args,
            },
        )
        app_sync_stack.schema.add_type(self.vpc_filter)
