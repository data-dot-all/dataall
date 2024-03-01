from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import CodeFirstSchema, ResolvableField, GraphqlType
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.core.environment_inputs import EnvironmentInputs
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.organization_types import OrganizationTypes
from stacks.schema.core.stack_types import StackTypes


@singleton
class EnvironmentQueries(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            data_source: LambdaDataSource,
            env_types: EnvironmentTypes,
            env_inputs: EnvironmentInputs,
            org_types: OrganizationTypes,
            stack_types: StackTypes,
    ):
        schema: CodeFirstSchema = api.schema
        self.get_environment = ResolvableField(
            return_type=env_types.environment.attribute(),
            args={'environmentUri': GraphqlType.string()},
            data_source=data_source,
        )
        schema.add_query('getEnvironment', self.get_environment)
        env_types.vpc.add_field(field_name='environment', field=self.get_environment)

        self.list_environments = ResolvableField(
            return_type=env_types.environment_search_result.attribute(),
            args={'filter': env_inputs.environment_filter.attribute()},
            data_source=data_source,
        )
        schema.add_query('listEnvironments', self.list_environments)
        org_types.organization.add_field(field_name='environment', field=self.list_environments)

        self.list_environment_networks = ResolvableField(
            return_type=env_types.vpc_search_result.attribute(),
            args={'environmentUri': GraphqlType.string(), 'filter': env_inputs.vpc_filter.attribute()},
            data_source=data_source,
        )
        schema.add_query('listEnvironmentNetworks', self.list_environment_networks)

        env_types.environment.add_field(field_name='networks', field=ResolvableField(
            return_type=env_types.vpc.attribute(is_list=True),
            args={'environmentUri': GraphqlType.string()},
            data_source=data_source,
        ))

        # env_types.environment.add_field(field_name='stack', field=ResolvableField(
        #     return_type=stack_types.stack.attribute(),
        #     args={'environmentUri': GraphqlType.string()},
        #     data_source=data_source,
        # ))

        env_types.environment.add_field(field_name='userRoleInEnvironment', field=ResolvableField(
            return_type=env_types.environment_permission.attribute(),
            args={'environmentUri': GraphqlType.string()},
            data_source=data_source,
        ))

        env_types.environment.add_field(field_name='parameters', field=ResolvableField(
            return_type=env_types.environment_parameter.attribute(is_list=True),
            args={'environmentUri': GraphqlType.string()},
            data_source=data_source,
        ))
