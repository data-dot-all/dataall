from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import CodeFirstSchema, ResolvableField
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.core.environment_inputs import EnvironmentInputs
from stacks.schema.core.environment_types import EnvironmentTypes


@singleton
class EnvironmentQueries(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            data_source: LambdaDataSource,
            env_types: EnvironmentTypes,
            env_inputs: EnvironmentInputs
    ):
        schema: CodeFirstSchema = api.schema
        self.list_environments = ResolvableField(
            return_type=env_types.environment_search_result.attribute(),
            args={'filter': env_inputs.environment_filter.attribute()},
            data_source=data_source,
        )
        schema.add_query('listEnvironments', self.list_environments)
