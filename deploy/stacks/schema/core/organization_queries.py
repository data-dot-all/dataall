from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import GraphqlType, CodeFirstSchema, ResolvableField
from injector import inject, singleton

from stacks.schema import SchemaBase
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

    ):
        schema: CodeFirstSchema = api.schema

        schema.add_query('listOrganizations', ResolvableField(
            return_type=org_types.organization_search_result.attribute(),
            args={'filter': org_inputs.organization_filter.attribute()},
            data_source=data_source,
        ))

        schema.add_query('getOrganization', ResolvableField(
            return_type=org_types.organization.attribute(),
            args={'organizationUri': GraphqlType.string()},
            data_source=data_source,
        ))
