from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import GraphqlType, CodeFirstSchema, ResolvableField
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.organization_inputs import OrganizationInputs
from stacks.schema.core.organization_types import OrganizationTypes


@singleton
class OrganizationQueries(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            data_source: LambdaDataSource,
            org_inputs: OrganizationInputs,
            org_types: OrganizationTypes,
            env_types: EnvironmentTypes,
    ):
        schema: CodeFirstSchema = api.schema

        schema.add_query('listOrganizations', ResolvableField(
            return_type=org_types.organization_search_result.attribute(),
            args={'filter': org_inputs.organization_filter.attribute()},
            # pipeline_config=[data_source_func],
            data_source=data_source,
            # code=Code.from_asset(str(Path(__file__).parent.parent.parent.joinpath('schema/function_code.js'))),
            # runtime=FunctionRuntime.JS_1_0_0,
        ))

        get_organization = ResolvableField(
            return_type=org_types.organization.attribute(),
            args={'organizationUri': GraphqlType.string()},
            data_source=data_source,
        )
        schema.add_query('getOrganization', get_organization)
        env_types.environment.add_field(field_name='organization', field=get_organization)

        org_types.organization.add_field(field_name='stats', field=ResolvableField(
            return_type=org_types.organization_stats.attribute(),
            data_source=data_source,
        ))

        org_types.organization.add_field(field_name='userRoleInOrganization', field=ResolvableField(
            return_type=org_types.organisation_user_role.attribute(),
            data_source=data_source,
        ))
