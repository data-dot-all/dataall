from aws_cdk.aws_appsync import GraphqlApi, LambdaDataSource
from awscdk.appsync_utils import GraphqlType, EnumType, CodeFirstSchema, ObjectType, ResolvableField
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes
from stacks.schema.core.environment_queries import EnvironmentQueries


@singleton
class OrganizationTypes(SchemaBase):
    @inject
    def __init__(
            self,
            api: GraphqlApi,
            data_source: LambdaDataSource,
            common_types: CommonTypes,
            env_queries: EnvironmentQueries,
    ):
        schema: CodeFirstSchema = api.schema

        organization_stats = ObjectType('OrganizationStats', definition={
            'groups': GraphqlType.int(),
            'users': GraphqlType.int(),
            'environments': GraphqlType.int(),
        })
        schema.add_type(organization_stats)

        self.organisation_user_role = EnumType('OrganisationUserRole', definition=[
            'Owner',
            'Admin',
            'Member',
            'NotMember',
            'Invited',
        ])
        schema.add_type(self.organisation_user_role)

        self.organization = ObjectType('Organization', definition={
            'organizationUri': GraphqlType.id(),
            'label': GraphqlType.string(),
            'name': GraphqlType.string(),
            'description': GraphqlType.string(),
            'tags': GraphqlType.string(is_list=True),
            'owner': GraphqlType.string(),
            'SamlGroupName': GraphqlType.string(),
            'userRoleInOrganization': ResolvableField(
                return_type=self.organisation_user_role.attribute(),
                data_source=data_source,
            ),
            'environments': env_queries.list_environments,
            'created': GraphqlType.string(),
            'updated': GraphqlType.string(),
            'stats': ResolvableField(
                return_type=organization_stats.attribute(),
                data_source=data_source,
            ),
        })
        schema.add_type(self.organization)

        self.organization_sort_field = EnumType('OrganizationSortField', definition=[
            'created',
            'updated',
            'label',
        ])
        schema.add_type(self.organization_sort_field)

        self.organization_search_result = ObjectType('OrganizationSearchResult', interface_types=[common_types.paged_result], definition={
            'nodes': self.organization.attribute(is_list=True)
        })
        schema.add_type(self.organization_search_result)
