from functools import cache

from awscdk.appsync_utils import GraphqlType, ResolvableField

from stacks.appsync import AppSyncStack
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.organization_inputs import OrganizationInputs
from stacks.schema.core.organization_types import OrganizationTypes


@cache
class OrganizationQueries:
    def __init__(
        self,
        app_sync_stack: AppSyncStack,
        org_inputs: OrganizationInputs,
        org_types: OrganizationTypes,
        env_types: EnvironmentTypes,
        **_kwargs,
    ):
        app_sync_stack.schema.add_query(
            'listOrganizations',
            ResolvableField(
                return_type=org_types.organization_search_result.attribute(),
                args={'filter': org_inputs.organization_filter.attribute()},
                # pipeline_config=[data_source_func],
                data_source=app_sync_stack.data_source,
                # code=Code.from_asset(str(Path(__file__).parent.parent.parent.joinpath('schema/function_code.js'))),
                # runtime=FunctionRuntime.JS_1_0_0,
            ),
        )

        get_organization = ResolvableField(
            return_type=org_types.organization.attribute(),
            args={'organizationUri': GraphqlType.string()},
            data_source=app_sync_stack.data_source,
        )
        app_sync_stack.schema.add_query('getOrganization', get_organization)
        env_types.environment.add_field(field_name='organization', field=get_organization)

        org_types.organization.add_field(
            field_name='stats',
            field=ResolvableField(
                return_type=org_types.organization_stats.attribute(),
                data_source=app_sync_stack.data_source,
            ),
        )

        org_types.organization.add_field(
            field_name='userRoleInOrganization',
            field=ResolvableField(
                return_type=org_types.organisation_user_role.attribute(),
                data_source=app_sync_stack.data_source,
            ),
        )
