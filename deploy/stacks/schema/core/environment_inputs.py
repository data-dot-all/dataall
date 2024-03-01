from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import CodeFirstSchema, InputType
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes
from stacks.schema.core.environment_types import EnvironmentTypes


@singleton
class EnvironmentInputs(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            common_types: CommonTypes,
            environment_types: EnvironmentTypes
    ):
        schema: CodeFirstSchema = api.schema

        environment_sort_criteria = InputType('EnvironmentSortCriteria', definition={
            'field': environment_types.environment_sort_field.attribute(),
            'direction': common_types.sort_direction.attribute(),
        })
        schema.add_type(environment_sort_criteria)

        self.environment_filter = InputType('EnvironmentFilter', definition={
            **common_types.filter_args,
            'roles': environment_types.environment_permission.attribute(is_list=True),
            'sort': environment_sort_criteria.attribute(is_list=True),
        })
        schema.add_type(self.environment_filter)

        self.vpc_filter = InputType('VpcFilter', definition={
            **common_types.filter_args,
        })
        schema.add_type(self.vpc_filter)
