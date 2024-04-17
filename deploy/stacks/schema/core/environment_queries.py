from awscdk.appsync_utils import ResolvableField, GraphqlType

from stacks.appsync import AppSyncStack
from stacks.schema.core.environment_inputs import EnvironmentInputs
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.organization_types import OrganizationTypes


class EnvironmentQueries:
    def __init__(
        self,
        app_sync_stack: AppSyncStack,
        env_types: EnvironmentTypes,
        env_inputs: EnvironmentInputs,
        org_types: OrganizationTypes,
        **kwargs,
    ):
        self.get_environment = ResolvableField(
            return_type=env_types.environment.attribute(),
            args={'environmentUri': GraphqlType.string()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('getEnvironment', self.get_environment)
        env_types.vpc.add_field(field_name='environment', field=self.get_environment)

        self.list_environments = ResolvableField(
            return_type=env_types.environment_search_result.attribute(),
            args={'filter': env_inputs.environment_filter.attribute()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('listEnvironments', self.list_environments)
        org_types.organization.add_field(field_name='environments', field=self.list_environments)

        self.list_environment_networks = ResolvableField(
            return_type=env_types.vpc_search_result.attribute(),
            args={'environmentUri': GraphqlType.string(), 'filter': env_inputs.vpc_filter.attribute()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('listEnvironmentNetworks', self.list_environment_networks)

        env_types.environment.add_field(
            field_name='networks',
            field=ResolvableField(
                return_type=env_types.vpc.attribute(is_list=True),
                args={'environmentUri': GraphqlType.string()},
                data_source=app_sync_stack.data_source,
            ),
        )

        # env_types.environment.add_field(field_name='stack', field=ResolvableField(
        #     return_type=stack_types.stack.attribute(),
        #     args={'environmentUri': GraphqlType.string()},
        #     data_source=data_source,
        # ))

        env_types.environment.add_field(
            field_name='userRoleInEnvironment',
            field=ResolvableField(
                return_type=env_types.environment_permission.attribute(),
                args={'environmentUri': GraphqlType.string()},
                data_source=app_sync_stack.data_source,
            ),
        )

        env_types.environment.add_field(
            field_name='parameters',
            field=ResolvableField(
                return_type=env_types.environment_parameter.attribute(is_list=True),
                args={'environmentUri': GraphqlType.string()},
                data_source=app_sync_stack.data_source,
            ),
        )
