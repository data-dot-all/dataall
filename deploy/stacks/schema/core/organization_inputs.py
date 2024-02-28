from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import GraphqlType, CodeFirstSchema, InputType
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes
from stacks.schema.core.organization_types import OrganizationTypes


@singleton
class OrganizationInputs(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            common_types: CommonTypes,
            org_types: OrganizationTypes,
    ):
        schema: CodeFirstSchema = api.schema

        self.new_organization_input = InputType('NewOrganizationInput', definition={
            'label': GraphqlType.string(),
            'description': GraphqlType.string(),
            'tags': GraphqlType.string(is_list=True),
            'SamlGroupName': GraphqlType.string(),
        })
        schema.add_type(self.new_organization_input)

        self.organization_sort_criteria = InputType('OrganizationSortCriteria', definition={
            'field': org_types.organization_sort_field.attribute(),
            'direction': common_types.sort_direction.attribute(),
        })
        schema.add_type(self.organization_sort_criteria)

        self.organization_filter = InputType('OrganizationFilter', definition={
            **common_types.filter_args,
            'sort': self.organization_sort_criteria.attribute(is_list=True),
            'roles': org_types.organisation_user_role.attribute(is_list=True),
        })
        schema.add_type(self.organization_filter)
