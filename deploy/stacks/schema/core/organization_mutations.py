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

        schema.add_mutation('createOrganization', ResolvableField(
            return_type=org_types.organization.attribute(),
            args={'input': org_inputs.new_organization_input.attribute()},
            data_source=data_source,
        ))
